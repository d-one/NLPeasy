"""Pipeline to preprocess raw data for training."""
from process import load_raw_df_and_save_raw_dataset


def main():
    """Load raw dataframe, convert to dataset and save."""
    load_raw_df_and_save_raw_dataset()


if __name__ == "__main__":
    main()
