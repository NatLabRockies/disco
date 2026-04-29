# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 09:03:51 2019

@author: ppaudyal
"""

# import pandas as pd


def calc_dist(loadandbus_, nodeanddistance):

    nodeanddistance["Node_only"] = ""
    for i in range(len(nodeanddistance)):
        tmp = nodeanddistance["Node"][i]
        nodeanddistance.loc[i,"Node_only"] = tmp[0:-2]
    
    nodeanddistance_ = nodeanddistance.drop_duplicates(
        subset="Node_only", keep="first"
    ).reset_index(drop=True)  # drop duplicates based on "Node_only" column  
    
    # if subset="Distance" then any two nodes could have same distance
    # print(nodeanddistance_.head(), "\n\n")
    # print(len(nodeanddistance_))

    # nodeanddistance_.index = range(len(nodeanddistance_))
    # print(nodeanddistance_.head())

    loadandbus_ = loadandbus_.copy()
    loadandbus_["Distance"] = None
    tmp_lst = nodeanddistance_["Node_only"].tolist()
    # print(tmp_lst) # testing
    for i in range(len(loadandbus_)):
        bus = str(loadandbus_["Bus"].iloc[i])
        if bus in tmp_lst:
            tmp_indx = tmp_lst.index(bus)  # the index of that node in the list
            loadandbus_.loc[i, "Distance"] = nodeanddistance_.loc[tmp_indx, "Distance"]
        else:
            print("No ", loadandbus_["Bus"][i], "\n")

    loadandbus_.to_csv("Load_distance_from_SS.csv")  # save as csv if required
    return loadandbus_
