import pandas as pd
import sys
import jellyfish

# command line arguments
official_ao_data_file = sys.argv[1]
oddsportal_ao_data_file = sys.argv[2]
flashscore_ao_data_file = sys.argv[3]

ao_df = pd.read_csv(official_ao_data_file, sep="\t") 
op_df = pd.read_csv(oddsportal_ao_data_file, sep="\t") 
fs_df = pd.read_csv(flashscore_ao_data_file, sep="\t") 

nrows_ao = len(ao_df.index)
nrows_op = len(op_df.index)
nrows_fs = len(fs_df.index)

"""
 how do we decide that it's the same match?
	1: same YEAR
	2: same SURNAMES of the players
"""

def get_ao_surname(st):

	# IN: a string like "Rafael Nadal"
	su = st[st.index(".") - 1] + st.split()[1][:2]

	# ignore all parts with the full stop
	# name_split = [w.strip().lower() for w in st.split() if "." not in w]   # ["Rafael", "Nadal"]

	
	# if len(name_split) == 1:
	# 	su = name_split[0][0]  # e.g. John -> j
	# else:  # John Watson -> jwa
	# 	su = name_split[0][0] + name_split[1][:2]
	# else:
	# 	if "del" in name_split:
	# 		su = "_".join(name_split[name_split.index("del"):])
	# 	elif "de" in name_split:
	# 		su = "_".join(name_split[name_split.index("de"):])
	# 	elif len(name_split) == 4:
	# 		su = " ".join(name_split[-2:])
	# 	else:
	# 		su = name_split[-1]

	#su = su.replace("-","_")
	# if "-" in su:
	# 	su = su.split("-")[0]

	return su.lower()

def get_op_surname(st):

	su = st[st.index(".") - 1] + st.split()[0][:2]

	# su = "_".join([w.strip().lower() for w in st.split() if "." not in w])

	# if "-" in su:
	# 	su = su.split("-")[0]
	
	return su.lower()

def normalize_name(st):

	st_split = st.split()

	if "." not in st_split[0]:
		nn = st_split[0][0] + "." + " " + st_split[1]
	else:
		nn = st_split[0] + " " + st_split[1]

	return nn

# date is either just a year or something like 2016-01-25
ao_df["year"] = ao_df.date.apply(lambda _: _ if "-" not in _ else _.split("-")[0]).astype(int)

ao_df.player1 = ao_df.player1.apply(lambda _: normalize_name(_) if "/" not in _ else "/".join([normalize_name(y) for y in _.split("/")]))
ao_df.player2 = ao_df.player2.apply(lambda _: normalize_name(_) if "/" not in _ else "/".join([normalize_name(y) for y in _.split("/")]))
# ao_df["player1"] = ao_df["player1"].apply(lambda _:  y.split()[0][0]+"."+" "+y for y in _.split("/") )
#where_2016 = (ao_df["year"] == 2016)
#where_not_2016 = ~ where_2016
# assume that surname is all but the very first word; special case: if there's del before the last word, then it's a part of surname
plist1 = ao_df.player1.apply(lambda _: [get_ao_surname(_)] if "/" not in _ else [get_ao_surname(y) for y in _.split("/")])
plist2 = ao_df.player2.apply(lambda _: [get_ao_surname(_)] if "/" not in _ else [get_ao_surname(y) for y in _.split("/")])

# plist1b = ao_df.player1.apply(lambda _: [get_op_surname(_)] if "/" not in _ else [get_op_surname(y) for y in _.split("/")])
# plist2b = ao_df.player2.apply(lambda _: [get_op_surname(_)] if "/" not in _ else [get_op_surname(y) for y in _.split("/")])


ao_df["id"] = pd.Series([y for y in map(lambda x: "_".join(x), map(sorted, [x[0]+x[1] for x in zip(plist1, plist2)]))]).values


# assume that everything except the bit with a dot is surname, e.g. de voest l.
plist1_op = op_df.player1.apply(lambda _: [get_op_surname(_)] if "/" not in _ else [get_op_surname(y) for y in _.split("/")])
plist2_op = op_df.player2.apply(lambda _: [get_op_surname(_)] if "/" not in _ else [get_op_surname(y) for y in _.split("/")])
op_df["id"] = pd.Series([y for y in map(lambda x: "_".join(x), map(sorted, [x[0]+x[1] for x in zip(plist1_op, plist2_op)]))]).values

# here dates are like 14 Jan 2009
op_df["year"] = op_df.date.apply(lambda _: _.split()[-1]).astype(int)

fs_df["year"] = fs_df.date.apply(lambda _: _.split("-")[0]).astype(int)

# op_df = op_df.append(fs_df, ignore_index=True)

min_year_op = op_df.year.min()
max_year_op = op_df.year.max()

starting_times = []
exact_match_idx = []
nomatch_idx = []
nomatch_absent_year_idx = []
mult_match_idx = []

nomatch_file = "nomatch.csv"
multmatch_file = "multmatch.csv"

for i in range(nrows_ao):

	print("matching {} vs {} played in {}...".format(plist1[i], plist2[i],ao_df.year[i]), end="")
	
	if ao_df.year[i] not in range(min_year_op, max_year_op + 1):
		print("skip")
		starting_times.append("N/A")
		nomatch_absent_year_idx.append(i)
		continue
	
	eindex = (op_df.year == ao_df.year[i]) & (op_df.id == ao_df.id[i])
	if sum(eindex) == 1:
		mindex = eindex
	else:
		mindex = op_df.year.isin([ao_df.year[i]]) & op_df.id.apply(lambda _: jellyfish.levenshtein_distance(ao_df.id[i], _) < 2)

	NMTCH = sum(mindex)

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

