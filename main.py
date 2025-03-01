from carddetails import CardDetails
from cardlist import CardList
from fusiontransformer import FusionTransformer


def main():
    # cl = CardList()
    # cl.run()

    # input_filename = "json/card_details.json"
    # output_filename = "ygo/dm1/fixtures/card_details_formatted.json"
    # model_name = "dm1.card"
    # cd = CardDetails()
    # cd.run()
    # cd.format_json(input_filename=input_filename, output_filename=output_filename, model_name=model_name)

    ft = FusionTransformer()
    ft.transform_file("json/fusions.json", "json/fusions_transformed.json")


if __name__ == "__main__":
    main()
