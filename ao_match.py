import pandas as pd
import sys
import jellyfish

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

def get_ao_surname(st):

	# IN: a string like "Rafael Nadal"

	name_split = [w.strip().lower() for w in st.split()]   # ["Rafael", "Nadal"]

	
	if len(name_split) == 1:
		su = name_split[0]
	elif len(name_split) == 2:  # just name and surname
		su = name_split[1]
	elif len(name_split) == 3:  # John William Coles
		if "del" == name_split[-2:-1] or "de" == name_split[-2:-1]:
			su = "_".join(name_split[-2:])
		else:  
			su = name_split[-1]
	else:  # long name like Antonio Sanchez Matilda Souza
		su = "_".join(name_split[1:])
	
	return su

def get_op_surname(st):

	su = "_".join([w.strip().lower() for w in st.split() if "." not in w])
	
	return su



# assume that surname is all but the very first word; special case: if there's del before the last word, then it's a part of surname
plist1 = ao_df.player1.apply(lambda _: [get_ao_surname(_)] if "/" not in _ else [get_ao_surname(y) for y in _.split("/")])
plist2 = ao_df.player2.apply(lambda _: [get_ao_surname(_)] if "/" not in _ else [get_ao_surname(y) for y in _.split("/")])
ao_df["id"] = pd.Series([y for y in map(lambda x: "_".join(x), map(sorted, [x[0]+x[1] for x in zip(plist1, plist2)]))]).values

# date is either just a year or something like 2016-01-25
ao_df["year"] = ao_df.date.apply(lambda _: _ if "-" not in _ else _.split("-")[0]).astype(int)

# assume that everything except the bit with a dot is surname, e.g. de voest l.
plist1 = op_df.player1.apply(lambda _: [get_op_surname(_)] if "/" not in _ else [get_op_surname(y) for y in _.split("/")])
plist2 = op_df.player2.apply(lambda _: [get_op_surname(_)] if "/" not in _ else [get_op_surname(y) for y in _.split("/")])
op_df["id"] = pd.Series([y for y in map(lambda x: "_".join(x), map(sorted, [x[0]+x[1] for x in zip(plist1, plist2)]))]).values

#print(op_df.id.head())

# # here dates are like 14 Jan 2009
op_df["year"] = op_df.date.apply(lambda _: _.split()[-1]).astype(int)

min_year_op = op_df.year.min()
max_year_op = op_df.year.max()

# # print("actual match starting times are available for years {} to {}".format(min_year_op, max_year_op))

# starting_times = []
# exact_match_idx = []
# nomatch_idx = []
# nomatch_absent_year_idx = []
# mult_match_idx = []

# nomatch_file = "nomatch.csv"
# multmatch_file = "multmatch.csv"

# def match_again(surname1_ao, surname2_ao, year_ao):

# 	# case 1: single
# 	if ("/" not in surname1_ao) and ("/" not in surname2_ao):
# 		singles_idx = ~ (op_df.sur_p1.apply(lambda _: "/" in _) & op_df.sur_p2.apply(lambda _: "/" in _))
		
# 		ii = op_df.year[singles_idx].isin([year_ao]) & (op_df.sur_p1[singles_idx].apply(lambda _: jellyfish.levenshtein_distance(surname1_ao, _) < 3) or 
# 				op_df.sur_p2[singles_idx].apply(lambda _: jellyfish.levenshtein_distance(surname1_ao, _) < 3)) & 
# 				([singles_idx][singles_idx].apply(lambda _: jellyfish.levenshtein_distance(surname2_ao, _) < 3) or 
# 				op_df.sur_p2[singles_idx].apply(lambda _: jellyfish.levenshtein_distance(surname2_ao, _) < 3)) 

# 		if sum(ii) == 1:
# 			print("matched: ",surname1_ao,"vs", surname2_ao,"to", op_df.sur_p1[ii],"vs",op_df.sur_p2[ii])


for i in range(nrows_ao):

	print("matching {} vs {} played in {}...".format(ao_df.sur_p1[i], ao_df.sur_p2[i],ao_df.year[i]), end="")
	
	if ao_df.year[i] not in range(min_year_op, max_year_op + 1):
		print("skip")
		starting_times.append("N/A")
		nomatch_absent_year_idx.append(i)
		continue

	# right_one = (
	# 	op_df.year.isin([ao_df.year[i]]) & 
	# 	op_df.sur_p1.apply(lambda _: len(_ & ao_df.sur_p1[i]) == len(_) or len(_ & ao_df.sur_p2[i]) == len(_)) & 
	# 	op_df.sur_p2.apply(lambda _: len(_ & ao_df.sur_p1[i]) == len(_) or len(_ & ao_df.sur_p2[i]) == len(_)) )
	
	right_one = (
		op_df.year.isin([ao_df.year[i]]) & 
		op_df.sur_p1.apply(  lambda _: (jellyfish.levenshtein_distance(_ ,ao_df.sur_p1[i][0]) < 3) or 
										(jellyfish.levenshtein_distance(_ ,ao_df.sur_p2[i][0]) < 3)  ) & 
		op_df.sur_p2.apply(  lambda _: jellyfish.levenshtein_distance(_ ,ao_df.sur_p1[i][0]) < 3 or 
											jellyfish.levenshtein_distance(_ ,ao_df.sur_p2[i][0]) < 3  ) )
	

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


# for i, s1 in enumerate(ao_df.sur_p1.iloc[nomatch_idx]):

# match_again(surname1_ao, surname2_ao, year_ao)


ao_df.iloc[nomatch_idx].to_csv(nomatch_file, index=False, sep="\t")
ao_df.iloc[mult_match_idx].to_csv(multmatch_file, index=False, sep="\t")
	# ao_df.sur_p1[i] is a list of 1 or 2 surnames

