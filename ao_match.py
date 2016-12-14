import pandas as pd
import sys

# command line arguments
official_ao_data_file = sys.argv[1]
oddsportal_ao_data_file = sys.argv[2]

ao_df = pd.read_csv(official_ao_data_file, sep="\t") 
op_df = pd.read_csv(oddsportal_ao_data_file, sep="\t") 

"""
 how do we decide that it's the same match?
	1: same YEAR
	2: same SURNAMES of the players
"""
print(list(ao_df))
print(ao_df.player1)

ff = ao_df.loc[:,"player1"].apply(lambda _: _.split()[1].strip().lower())

print(ff.head())
