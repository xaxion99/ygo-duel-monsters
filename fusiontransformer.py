import json
import os

class FusionTransformer:
    @staticmethod
    def split_name_field(full_name):
        """
        Splits a string like "002: Mystical Elf" into a tuple (number, name).
        Removes any leading '#' in the number.
        """
        try:
            number_part, name_part = full_name.split(":", 1)
            number_part = number_part.strip().lstrip("#")
            # Convert to int to remove any leading zeros and then back to string.
            number = str(int(number_part))
            name = name_part.strip()
        except ValueError:
            # In case splitting fails, return empty number and full name as name.
            number = ""
            name = full_name.strip()
        return number, name

    @staticmethod
    def transform_material(material):
        """
        Transforms a material entry.
        If the material is a string, split it into a dict with "Number" and "Name".
        If it is a list, do so for each element.
        """
        if isinstance(material, str):
            num, name = FusionTransformer.split_name_field(material)
            return {"Number": num, "Name": name}
        elif isinstance(material, list):
            return [
                {
                    "Number": FusionTransformer.split_name_field(item)[0],
                    "Name": FusionTransformer.split_name_field(item)[1]
                }
                for item in material
            ]
        else:
            # If it's not a string or list, return it as-is.
            return material

    @classmethod
    def transform_fusion_object(cls, obj):
        """
        Transforms one fusion object by splitting its "Name" field and
        transforming its Materials entries.
        """
        new_obj = {}
        # Split main Name field
        main_name = obj.get("Name", "")
        number, name = cls.split_name_field(main_name)
        new_obj["Number"] = number
        new_obj["Name"] = name

        # Process Materials (a list of dictionaries)
        new_materials = []
        for material_dict in obj.get("Materials", []):
            new_material_dict = {}
            for key, value in material_dict.items():
                new_material_dict[key] = cls.transform_material(value)
            new_materials.append(new_material_dict)
        new_obj["Materials"] = new_materials
        return new_obj

    def transform_file(self, input_file, output_file):
        """
        Loads the original JSON data from input_file, transforms each object,
        and writes out the transformed data to output_file.
        """
        with open(input_file, "r", encoding="utf-8") as infile:
            data = json.load(infile)

        transformed_data = [self.transform_fusion_object(obj) for obj in data]

        with open(output_file, "w", encoding="utf-8") as outfile:
            json.dump(transformed_data, outfile, indent=4, ensure_ascii=False)

        print(f"Transformation complete. See {output_file}.")

    def convert_to_fixture_format(SELF, input_filename, output_filename):
        model_name = "dm1.fusion"
        with open(input_filename, "r", encoding="utf-8") as infile:
            data = json.load(infile)

        fixture_list = []
        pk = 1
        for fusion in data:
            fixture_obj = {
                "model": model_name,
                "pk": pk,
                "fields": {
                    "number": fusion.get("Number", ""),
                    "name": fusion.get("Name", ""),
                    "materials": fusion.get("Materials", [])
                }
            }
            fixture_list.append(fixture_obj)
            pk += 1

        with open(output_filename, "w", encoding="utf-8") as outfile:
            json.dump(fixture_list, outfile, indent=4, ensure_ascii=False)
        print(f"Converted {len(fixture_list)} objects to fixture format in '{output_filename}'.")

    def parse_material(self, material_entry):
        """
        Given a material entry that can be a dict or a list, return a list of card numbers.
        Assumes each material entry is a dict with keys "Number" and "Name".
        Converts the number to an integer if possible.
        """
        result = []
        if isinstance(material_entry, dict):
            num = material_entry.get("Number", "").strip()
            try:
                result.append(int(num))
            except ValueError:
                # If conversion fails, store as-is (or skip)
                result.append(num)
        elif isinstance(material_entry, list):
            for item in material_entry:
                num = item.get("Number", "").strip()
                try:
                    result.append(int(num))
                except ValueError:
                    result.append(num)
        return result


    def run(self):
        input_file = "json/fusions_fixture.json"

        if not os.path.exists(input_file):
            print(f"Input file '{input_file}' not found!")
            return

        # Load the fixture JSON (which is a list of fixture objects)
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        fusion_fixtures = []
        fusion_material_group_fixtures = []

        # We'll use a counter for FusionMaterialGroup primary keys
        material_group_pk = 1

        for obj in data:
            # Our fusion object is in Django fixture format:
            # { "model": "dm1.fusion", "pk": X, "fields": { "number": "...", "name": "...", "materials": [...] } }
            fusion_pk = obj.get("pk")
            fields = obj.get("fields", {})
            fusion_number = fields.get("number", "")
            fusion_name = fields.get("name", "")
            materials = fields.get("materials", [])

            # Build a new fixture for the Fusion model (excluding materials)
            fusion_fixture = {
                "model": "dm1.fusion",
                "pk": fusion_pk,
                "fields": {
                    "number": fusion_number,
                    "name": fusion_name,
                    "result_card": None  # Adjust if you have a value
                }
            }
            fusion_fixtures.append(fusion_fixture)

            # For each material group in this fusion:
            for group in materials:
                # Note: the keys here are case sensitive; your sample uses "Material1" and "Material2"
                m1_entry = group.get("Material1")
                m2_entry = group.get("Material2")

                material1_list = self.parse_material(m1_entry)
                material2_list = self.parse_material(m2_entry)

                material_group_fixture = {
                    "model": "dm1.fusionmaterialgroup",
                    "pk": material_group_pk,
                    "fields": {
                        "fusion": fusion_pk,  # ForeignKey to Fusion
                        "material1": material1_list,
                        "material2": material2_list
                    }
                }
                fusion_material_group_fixtures.append(material_group_fixture)
                material_group_pk += 1

        # Write out the new fixture files
        with open("ygo/dm1/fixtures/fusions_fixture_fusions.json", "w", encoding="utf-8") as out_f:
            json.dump(fusion_fixtures, out_f, indent=4, ensure_ascii=False)
        print("Wrote Fusion fixture data to 'json/fusions_fixture_fusions.json'")

        with open("ygo/dm1/fixtures/fusions_fixture_material_groups.json", "w", encoding="utf-8") as out_mg:
            json.dump(fusion_material_group_fixtures, out_mg, indent=4, ensure_ascii=False)
        print("Wrote FusionMaterialGroup fixture data to 'json/fusions_fixture_material_groups.json'")
