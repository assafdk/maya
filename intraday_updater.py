import time
import tase

def main():
    print("Hey! I'm running here...")
    time.sleep(3)

    # Build TASE stocks lookup table
    stocks_df = tase.build_master_stock_df()
    # Get & append new intra_day data
    intraday_dir_path = '/Users/assafdekel/other_projects/maya/intraday'
    tase.get_all_todays_intraday_to_files(stocks_df, dir_path=intraday_dir_path)

    print("That's it, I'm done. Bye.")


if __name__ == "__main__":
    main()