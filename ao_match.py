import pandas as pd
import sys
from unidecode import unidecode
import jellyfish

# command line arguments
official_ao_data_file = sys.argv[1]
oddsportal_ao_data_file = sys.argv[2]
flashscore_ao_data_file = sys.argv[3]

player_surname_dict = {}

nlets = 3

"""
examples of names in the AO data:

Maria Kirilenko/Lina Krasnoroutskaya
Ma. Emilia Salerni/Milagros Sequera
Alex Jr. Bogomolov
Alex Bogomolov Jr.

and in ** 2016 **: G. Dabrowski/A. Rosolska, J. Tsonga

TODO: 
(1) remove all the parts with "."
(2) in what's left, if "-" is in the last word, remove the second part of the last word, i.e. Hubba-Whakka -> Hubba
(nlets) leave only the last word as the name
"""

def create_ao_single_id(pl1, pl2, yr):

	# names like Juan Cartlos del Morelos

	last_word_pl1 = [unidecode(w).lower() for w in pl1.split() if "." not in w][-1]
	last_word_pl2 = [unidecode(w).lower() for w in pl2.split() if "." not in w][-1]

	# what if there's a dash, i.e. "-"

	possible_surnames_pl1 = [w for w in last_word_pl1.split("-")]  # can be just ["clarke"] or ["clarke", "fatcat"]
	possible_surnames_pl2 = [w for w in last_word_pl2.split("-")]

	id_list = ["_".join(["_".join(sorted([p1]+[p2])), yr]) for p1 in possible_surnames_pl1 for p2 in possible_surnames_pl2]

	return id_list

def create_ao_double_id(pair1, pair2, yr):

	p1_pl1, p1_pl2 = pair1.split("/")
	p2_pl1, p2_pl2 = pair2.split("/")

	# names like Juan Cartlos del Morelos

	last_word_p1_pl1 = [unidecode(w).lower() for w in p1_pl1.split() if "." not in w][-1]
	last_word_p1_pl2 = [unidecode(w).lower() for w in p1_pl2.split() if "." not in w][-1]
	last_word_p2_pl1 = [unidecode(w).lower() for w in p2_pl1.split() if "." not in w][-1]
	last_word_p2_pl2 = [unidecode(w).lower() for w in p2_pl2.split() if "." not in w][-1]

	# what if there's a dash, i.e. "-"

	possible_surnames_p1_pl1 = [w for w in last_word_p1_pl1 .split("-")]  # can be just ["clarke"] or ["clarke", "fatcat"]
	possible_surnames_p1_pl2 = [w for w in last_word_p1_pl2 .split("-")]
	possible_surnames_p2_pl1 = [w for w in last_word_p2_pl1 .split("-")]
	possible_surnames_p2_pl2 = [w for w in last_word_p2_pl2 .split("-")]

	id_list = ["_".join(["_".join(sorted([p1]+[p2]+[p3]+[p4])), yr]) for p1 in possible_surnames_p1_pl1
															for p2 in possible_surnames_p1_pl2
															for p3 in possible_surnames_p2_pl1
															for p4 in possible_surnames_p2_pl2]

	return id_list


def normalize_name(st, nchars):

	st_wo_dots = [unidecode(w) for w in st.split() if "." not in w]
	
	if len(st_wo_dots) == 1:

		if "-" in st_wo_dots[0]:
			st_normalized = st_wo_dots[0].split("-")[0]
		else:
			st_normalized = st_wo_dots[0]
	
	elif len(st_wo_dots) == 2: # if 2 words left, like Pedro Martinez-Poppulis

		if "-" in st_wo_dots[1]:
			st_normalized = st_wo_dots[1].split("-")[0]
		else:
			st_normalized = st_wo_dots[1]

	elif len(st_wo_dots) == nlets:  # like Juan de Giggio

		if "-" in st_wo_dots[2]:
			st_normalized = st_wo_dots[2].split("-")[0]
		else:
			st_normalized = st_wo_dots[2]

	elif len(st_wo_dots) == 4:  # Juan Martin del Potro

		if "-" in st_wo_dots[nlets]:
			st_normalized = st_wo_dots[nlets].split("-")[0]
		else:
			st_normalized = st_wo_dots[nlets]
	else:

		st_normalized = st  # do nothing then

	return st_normalized.lower()[:nchars]

def process_df(df):

	nr0 = len(df.index)

	df = df.drop_duplicates()

	df.reset_index(inplace=True)

	nr1 = len(df.index)

	print("found {} duplicates".format(nr0-nr1))

	return df

ao_df = pd.read_csv(official_ao_data_file, sep="\t") 
op_df = pd.read_csv(oddsportal_ao_data_file, sep="\t") 
fs_df = pd.read_csv(flashscore_ao_data_file, sep="\t") 

ao_df = process_df(ao_df)
op_df = process_df(op_df)
fs_df = process_df(fs_df)

nrows_op = len(op_df.index)
nrows_fs = len(fs_df.index)
nrows_ao = len(ao_df.index)

print("have {} matches from the official AO web site, {} from OddsPortal and {} from Flashscore..".format(nrows_ao, nrows_op, nrows_fs))

#sys.exit("haha")

# date is either just a year or something like 2016-01-25
ao_years = ao_df.date.apply(lambda _: _ if "-" not in _ else _.split("-")[0]).tolist()

# plist1 = ao_df.player1.apply(lambda _: normalize_ao_names(_) if "/" not in _ else normalize_ao_names(y) for y in _.split("/"))
# plist2 = ao_df.player2.apply(lambda _: normalize_ao_names(_) if "/" not in _ else normalize_ao_names(y) for y in _.split("/"))

lis = []

for i in range(nrows_ao):

	if not "/" in ao_df.player1[i]:
		lis.append(create_ao_single_id(ao_df.player1[i], ao_df.player2[i], ao_years[i]))
	else:
		lis.append(create_ao_double_id(ao_df.player1[i], ao_df.player2[i], ao_years[i]))

print(lis)
#print("player lists for AO: {} and {}, year list {}".format(len(plist1), len(plist2),len(ao_years)))

sys.exit("haha")

ao_df["id"] = pd.Series([y for y in map(lambda x: "_".join(x), map(sorted, [x[0]+x[1]+[x[2]] for x in zip(plist1, plist2, ao_years)]))]).values

# here dates are like 14 Jan 2009
op_years = op_df.date.apply(lambda _: _.split()[-1]).tolist()

plist1_op = op_df.player1.apply(lambda _: [normalize_name(_, nlets)] if "/" not in _ else [normalize_name(y, 2) for y in _.split("/")])
plist2_op = op_df.player2.apply(lambda _: [normalize_name(_, nlets)] if "/" not in _ else [normalize_name(y, 2) for y in _.split("/")])

op_df["id"] = pd.Series([y for y in map(lambda x: "_".join(x), map(sorted, [x[0]+x[1]+[x[2]] for x in zip(plist1_op, plist2_op, op_years)]))]).values

# 2011-01-19
fs_years = fs_df.date.apply(lambda _: _.split("-")[0]).tolist()
plist1_fs = fs_df.player1.apply(lambda _: [normalize_name(_, nlets)] if "/" not in _ else [normalize_name(y, 2) for y in _.split("/")])
plist2_fs = fs_df.player2.apply(lambda _: [normalize_name(_, nlets)] if "/" not in _ else [normalize_name(y, 2) for y in _.split("/")])
fs_df["id"] = pd.Series([y for y in map(lambda x: "_".join(x), map(sorted, [x[0]+x[1]+[x[2]] for x in zip(plist1_fs, plist2_fs, fs_years)]))]).values


ao_df["year"] = pd.Series(ao_years).astype(int)

op_df["year"] = pd.Series(op_years).astype(int)
fs_df["year"] = pd.Series(fs_years).astype(int)

compare_df = pd.concat([op_df.loc[:, ["year", "time","id"]], fs_df.loc[:, ["year", "time","id"]]])

compare_df = compare_df.drop_duplicates(subset=["id"])

compare_df.year = compare_df.year.astype(int)
print("merged the OddsPortal and Flashscore, obtained {} records in total...".format(len(compare_df.index)))

min_year_op = compare_df["year"].min()
max_year_op = compare_df["year"].max()

print("available years with starting times: from {} to {}...".format(min_year_op, max_year_op))

starting_times = []
exact_match_idx = []
nomatch_idx = []
nomatch_absent_year_idx = []
mult_match_idx = []

nomatch_file = "nomatch.csv"
multmatch_file = "multmatch.csv"
res_file = "ao_matches.csv"

for i in range(nrows_ao):
	# print("i=",i)
	# print("plist2[i]=",plist2[i])
	# print("plist1[i]=",plist1[i])
	
	# print("ao_df.year[i]=",ao_df.year[i])

	print("matching {} vs {} played in {}...".format(plist1[i], plist2[i], ao_df.year[i]), end="")
	#print("this one has id=",ao_df.id[i])

	if ao_df.year[i] not in range(min_year_op, max_year_op + 1):
		print("skip")
		starting_times.append("N/A")
		nomatch_absent_year_idx.append(i)
		continue
	
	eindex = compare_df.id.apply(lambda _: _ == ao_df.id[i])

	if sum(eindex) == 1:

		mindex = eindex

	else:

		mindex =  compare_df.id.apply(lambda _: jellyfish.levenshtein_distance(ao_df.id[i][5:], _) < 2)

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


ao_df.iloc[nomatch_idx].to_csv(nomatch_file, index=False, sep="\t")
ao_df.iloc[mult_match_idx].to_csv(multmatch_file, index=False, sep="\t")
	# ao_df.sur_p1[i] is a list of 1 or 2 surnames

