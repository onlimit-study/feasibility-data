# import polars as pl
import seedcase_sprout as sp

# from scripts.package_properties import package_properties

# from scripts.resource_properties import resource_properties


def main():
    """Run the build pipeline of the data package."""
    ## PROPERTIES

    ## Create the properties script in default location if it doesn't already exist.
    sp.create_properties_script()

    ## Load your raw, but tidy, data into a Polars DataFrame.
    # package_path = sp.PackagePath()
    # raw_data = pl.read_csv(package_path.root() / "raw" / "data.csv")
    ## Extract field properties from the data.
    # field_properties = sp.extract_field_properties(data=raw_data)

    ## Create the resource properties script if it doesn't already exist.
    # sp.create_resource_properties_script(
    #     resource_name="",
    #     fields=field_properties,
    # )

    ## Save the properties to `datapackage.json`.
    # sp.write_properties(properties=package_properties)

    ## README

    ## Create the README text for the data package.
    # readme_text = sp.as_readme_text(package_properties)
    ## Write the README text to a `README.md` file.
    # sp.write_file(readme_text, package_path.readme())

    ## BATCH DATA

    ## Save the batch data.
    # sp.write_resource_batch(
    #     data=raw_data, resource_properties=resource_properties
    # )

    ## RESOURCE DATA

    ## Read in all the batch data files for the resource as a list.
    # batch_data = sp.read_resource_batches(
    #     resource_properties=resource_properties
    # )
    ## Join them all together into a single Polars DataFrame.
    # joined_data = sp.join_resource_batches(
    #     data_list=batch_data, resource_properties=resource_properties
    # )
    ## Write the resource data file.
    # sp.write_resource_data(
    #     data=joined_data, resource_properties=resource_properties
    # )


if __name__ == "__main__":
    main()
