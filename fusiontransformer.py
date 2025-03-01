import json


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