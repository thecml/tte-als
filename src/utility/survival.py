import numpy as np
import pandas as pd
from sklearn.utils import shuffle
from skmultilearn.model_selection import iterative_train_test_split
from sklearn.model_selection import train_test_split

def split_time_event(y):
    y_t = np.array(y['time'])
    y_e = np.array(y['event'])
    return (y_t, y_e)

def convert_to_structured(T, E):
    default_dtypes = {"names": ("event", "time"), "formats": ("bool", "i4")}
    concat = list(zip(E, T))
    return np.array(concat, dtype=default_dtypes)

def multilabel_train_test_split(X, y, test_size, random_state=None):
    """Iteratively stratified train/test split
    (Add random_state to scikit-multilearn iterative_train_test_split function)
    See this paper for details: https://link.springer.com/chapter/10.1007/978-3-642-23808-6_10
    """
    X, y = shuffle(X, y, random_state=random_state)
    X_train, y_train, X_test, y_test = iterative_train_test_split(X, y, test_size=test_size)
    return X_train, y_train, X_test, y_test

def make_stratified_split(
        df: pd.DataFrame,
        stratify_colname: str = 'event',
        frac_train: float = 0.5,
        frac_valid: float = 0.0,
        frac_test: float = 0.5,
        random_state: int = None
) -> (pd.DataFrame, pd.DataFrame, pd.DataFrame):
    '''Courtesy of https://github.com/shi-ang/BNN-ISD/tree/main'''
    assert frac_train >= 0 and frac_valid >= 0 and frac_test >= 0, "Check train validation test fraction."
    frac_sum = frac_train + frac_valid + frac_test
    frac_train = frac_train / frac_sum
    frac_valid = frac_valid / frac_sum
    frac_test = frac_test / frac_sum

    X = df.values  # Contains all columns.
    columns = df.columns
    if stratify_colname == 'event':
        stra_lab = df[stratify_colname]
    elif stratify_colname == 'time':
        stra_lab = df[stratify_colname]
        bins = np.linspace(start=stra_lab.min(), stop=stra_lab.max(), num=20)
        stra_lab = np.digitize(stra_lab, bins, right=True)
    elif stratify_colname == "both":
        t = df["time"]
        bins = np.linspace(start=t.min(), stop=t.max(), num=20)
        t = np.digitize(t, bins, right=True)
        e = df["event"]
        stra_lab = np.stack([t, e], axis=1)
    else:
        raise ValueError("unrecognized stratify policy")

    x_train, _, x_temp, y_temp = multilabel_train_test_split(X, y=stra_lab, test_size=(1.0 - frac_train),
                                                             random_state=random_state)
    if frac_valid == 0:
        x_val, x_test = [], x_temp
    else:
        x_val, _, x_test, _ = multilabel_train_test_split(x_temp, y=y_temp,
                                                          test_size=frac_test / (frac_valid + frac_test),
                                                          random_state=random_state)
    df_train = pd.DataFrame(data=x_train, columns=columns)
    df_val = pd.DataFrame(data=x_val, columns=columns)
    df_test = pd.DataFrame(data=x_test, columns=columns)
    assert len(df) == len(df_train) + len(df_val) + len(df_test)
    return df_train, df_val, df_test