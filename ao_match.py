import pandas as pd
import sys

# command line arguments
official_ao_data_file = sys.argv[1]
oddsportal_ao_data_file = sys.argv[2]

ao_df = pd.read_csv(official_ao_data_file, sep="\t") 
op_df = pd.read_csv(oddsportal_ao_data_file, sep="\t") 

nrows_ao = len(ao_df.index)
nrows_op = len(op_df.index)

# print("have {} match records from the AO web site and {} from OddsPortal...".format(nrows_ao, nrows_op))

"""
 how do we decide that it's the same match?
	1: same YEAR
	2: same SURNAMES of the players
"""

ao_df.sur_p1 = ao_df.player1.apply(lambda _: {_.split()[1].strip().lower()} if "/" not in _ else {y.split()[1].strip().lower() for y in _.split("/")})
ao_df.sur_p2 = ao_df.player2.apply(lambda _: {_.split()[1].strip().lower()} if "/" not in _ else {y.split()[1].strip().lower() for y in _.split("/")})

# date is either just a year or something like 2016-01-25
ao_df.year = ao_df.date.apply(lambda _: _ if "-" not in _ else _.split("-")[0]).astype(int)

op_df.sur_p1 = op_df.player1.apply(lambda _: {_.split()[0].strip().lower()} if "/" not in _ else {y.split()[0].strip().lower() for y in _.split("/")})
op_df.sur_p2 = op_df.player2.apply(lambda _: {_.split()[0].strip().lower()} if "/" not in _ else {y.split()[0].strip().lower() for y in _.split("/")})

# here dates are like 14 Jan 2009
op_df.year = op_df.date.apply(lambda _: _.split()[-1]).astype(int)

min_year_op = op_df.year.min()
max_year_op = op_df.year.max()

# print("actual match starting times are available for years {} to {}".format(min_year_op, max_year_op))

starting_times = []
exact_match_idx = []
nomatch_idx = []
nomatch_absent_year_idx = []
mult_match_idx = []


for i in range(nrows_ao):

	print("matching {} vs {} played in {}...".format(ao_df.sur_p1[i], ao_df.sur_p2[i],ao_df.year[i]), end="")
	
	if ao_df.year[i] not in range(min_year_op, max_year_op + 1):
		print("skip")
		starting_times.append("N/A")
		nomatch_absent_year_idx.append(i)
		continue

	#same_year = op_df.year.isin([ao_df.year[i]])
	#print(same_year)

	#ao_sur_set = ao_df.sur_p1[i] | ao_df.sur_p2[i]

	#print("ao players in this match:",format(ao_sur_set))
	# print("looking for year", ao_df.year[i])
	# print(op_df.year)
	#same_year = op_df.year.isin([ao_df.year[i]])
	#print("found same year records:", sum(same_year))

	right_one = (
		op_df.year.isin([ao_df.year[i]]) & 
		op_df.sur_p1.apply(lambda _: len(_ & ao_df.sur_p1[i]) == len(_) or len(_ & ao_df.sur_p2[i]) == len(_)) & 
		op_df.sur_p2.apply(lambda _: len(_ & ao_df.sur_p1[i]) == len(_) or len(_ & ao_df.sur_p2[i]) == len(_)) )
	

	#players_in_player2 = op_df.sur_p2.apply(lambda _: len(_ & ao_sur_set) == len(_))

	#print("same year and same pl2", op_df.sur_p2[same_year & players_in_player2])


	# intersection of ao_sur_set with the right match players 1 and 2 must be non-empty
	#right_one = same_year & players_in_player1 & players_in_player2
	NMTCH = sum(right_one)

	if NMTCH == 1:  # exactly 1 match
		print("ok")
		exact_match_idx.append(i)
	elif NMTCH == 0:
		print("no")
		nomatch_idx.append(i)
		starting_times.append("N/A")
	else:
		print("x{}!".format(NMTCH))
		mult_match_idx.append(i)

print("---> summary")
print("total ao matches: {}".format(nrows_ao))
print("total played before {}: {}".format(min_year_op, len(nomatch_absent_year_idx)))
print("successfully added time: {} ({}%)".format(len(exact_match_idx), round(100* len(exact_match_idx)/(nrows_ao - len(nomatch_absent_year_idx)), 1)))
print("couldn't find time: {}".format(len(nomatch_idx)))
print("multiple times found: {}".format(len(mult_match_idx)))

print("multiple match")
print(ao_df.iloc[mult_match_idx])
	# ao_df.sur_p1[i] is a list of 1 or 2 surnames

