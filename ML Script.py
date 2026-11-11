import pandas as pd
import numpy as np
import gc

# Helper functions

def to_decimal_year(x):
    dt = pd.to_datetime(x)
    year = dt.dt.year

    year_start = pd.to_datetime(year.astype(str) + '-01-01')
    next_year_start = pd.to_datetime((year + 1).astype(str) + '-01-01')
    return (dt - year_start) / (next_year_start - year_start) + year

# Reduction of memory usage (for numerical variables)
def reduce_mem_size(df, verbose = True):
    num_types = ['int8', 'int16', 'int32', 'int64', 'float16',
                 'float32', 'float64']

    if verbose:
        old_mem = (df.memory_usage().sum() / 1024**2).item()

    for col in df.columns:
        col_type = str(df[col].dtypes)
        if (col_type in num_types) & (col != 'Value') & (col != 'Price'):
            col_min = df[col].min()
            col_max = df[col].max()
            if col_type[:3] == 'int':
                if (col_min >= np.iinfo('int8').min) & (col_max <= np.iinfo('int8').max):
                    df[col] = df[col].astype('int8')
                elif (col_min >= np.iinfo('int16').min) & (col_max <= np.iinfo('int16').max):
                    df[col] = df[col].astype('int16')
                elif (col_min >= np.iinfo('int32').min) & (col_max <= np.iinfo('int32').max):
                    df[col] = df[col].astype('int32')
                else:
                    df[col] = df[col].astype('int64')
            else:
                if (col_min >= np.finfo('float32').min) & (col_max <= np.finfo('float32').max):
                    df[col] = df[col].astype('float32')
                else:
                    df[col] = df[col].astype('float64')

    if verbose:
        new_mem = (df.memory_usage().sum() / 1024**2).item()
        print(f'Old memory usage: {old_mem:.2f}MB; new memory usage: {new_mem:.2f}MB; reduction of {(abs(new_mem - old_mem)):.2f}MB ({(100 * (abs(new_mem - old_mem)) / old_mem):.2f}%)')

    return df

# Saves memory by adding to existing df1 instead of creating entirely merged df
def concat_merge(df1, df2, merge_on):
    merged_df = df1[merge_on]
    merged_df = merged_df.merge(df2, on = merge_on, how = 'left')
    new_cols = [col for col in list(merged_df) if col not in merge_on]
    df1[new_cols] = merged_df[new_cols]
    return df1

def create_time_variables(df):
    df['Day'] = df['Timestamp'].dt.day
    df['Month'] = df['Timestamp'].dt.month
    df['Weekday'] = df['Timestamp'].dt.day_of_week + 1
    df['Year'] = df['Timestamp'].dt.year
    df['Date'] = df['Timestamp'].dt.date

    df['Max_Day'] = df.groupby(['Year', 'Month'])['Day'].transform('max')
    df.loc[df['Max_Day'] == 8, 'Max_Day'] = 30

    df['Rel_Day_Month'] = (df['Day'] - 1) / (df['Max_Day'] - 1)

    df['Clock'] = df['Timestamp'].dt.time
    df['Hour'] = df['Clock'].apply(lambda x: int(str(x)[:2]))
    df['Minute'] = df['Clock'].apply(lambda x: int(str(x)[3:5]))
    df = df.drop(['Timestamp', 'Clock'], axis = 1)

    df['N_Elem_Day'] = df.groupby(['Year', 'Month', 'Day'])['Minute'].transform('count')
    print(df['N_Elem_Day'].unique())   # Checks out
    df['Time_Point_In_Day'] = df.groupby(['Year', 'Month', 'Day']).cumcount() + 1
    df['Rel_Time_Day'] = (df['Time_Point_In_Day'] - 1) / (df['N_Elem_Day'] - 1)
    df['Dec_Year'] = to_decimal_year(df['Date'])
    df = df.drop(['Date'], axis = 1)

    df = reduce_mem_size(df, verbose = False)
    df.to_feather('time-variables.feather')
    del(df)
    gc.collect()    
    

# Load data
dataset = pd.read_feather('German_Energy_Consumption_20181001_to_20261108.feather')
dataset['Time'] = dataset.index.astype(int) + 1    # Time index (acts also as ID for observations)
dataset = reduce_mem_size(dataset)

# Create data frame with time-related variables
create_time_variables(dataset[['Timestamp', 'Time']])

# Price variables
price_df = pd.read_feather('German_Energy_Market_Price_20181001_to_20261108.feather')
price_df = price_df.rename(columns = {'Value': 'Price'})
price_df['Time'] = price_df.index.astype(int) + 1
price_df = reduce_mem_size(price_df)

price_df['Year'] = price_df['Timestamp'].dt.year
price_df['Month'] = price_df['Timestamp'].dt.month
price_df['Week'] = price_df['Timestamp'].dt.isocalendar().week
price_df['Day'] = price_df['Timestamp'].dt.day
price_df['Max_Price_Year'] = price_df.groupby(['Year'])['Price'].transform('max')
price_df['Min_Price_Year'] = price_df.groupby(['Year'])['Price'].transform('min')
price_df['Max_Price_Month'] = price_df.groupby(['Year', 'Month'])['Price'].transform('max')
price_df['Min_Price_Month'] = price_df.groupby(['Year', 'Month'])['Price'].transform('min')
price_df['Max_Price_Week'] = price_df.groupby(['Year', 'Week'])['Price'].transform('max')
price_df['Min_Price_Week'] = price_df.groupby(['Year', 'Week'])['Price'].transform('min')
price_df['Max_Price_Day'] = price_df.groupby(['Year', 'Month', 'Day'])['Price'].transform('max')
price_df['Min_Price_Day'] = price_df.groupby(['Year', 'Month', 'Day'])['Price'].transform('min')
