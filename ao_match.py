import pandas as pd
import sys
from unidecode import unidecode
import jellyfish
import re

# data from the official AO web site
official_ao_data_file = "./data/scraped_data_from_aopen_WD_MD_MS_WS.csv"
# data from OddsPortal.com
oddsportal_ao_data_file = "./data/scraped_oddportal_data_MS_WS_MD_WD_2009_2016.csv"
# data from FlashScore.com
flashscore_ao_data_file = "./data/scraped_flashscore_data_WD_MD_MS_WS_2005_2016.csv"

# read the data
ao_df = pd.read_csv(official_ao_data_file, sep="\t") 
op_df = pd.read_csv(oddsportal_ao_data_file, sep="\t") 
fs_df = pd.read_csv(flashscore_ao_data_file, sep="\t") 

# remove possible duplicates
ao_df = ao_df.drop_duplicates()
ao_df.reset_index(inplace=True)

op_df = op_df.drop_duplicates()
op_df.reset_index(inplace=True)

fs_df = fs_df.drop_duplicates()
fs_df.reset_index(inplace=True)

print("rows in AO data: {}, OddsPortal: {}, FlashScore: {}".format(len(ao_df.index), len(op_df.index), len(fs_df.index)))

def get_player_surnames(player_name):

	"""
	IN:  player name, like Ednumdo Jr de la Pollo-Garcia
	OUT: a list of possible player surnames, like ["pollo", "garcia"]
	
	"""
	# name changes:
	# Kops-Jones -> Atawo
	player_name = re.sub(r"[Kk]ops[\s-][Jj]ones", "Atawo ", player_name)
	# remove [Capital Letter][dot or dash] like in W. or J-
	player_name = re.sub(r"[A-Z][.-]", " ", player_name)
	# remove [Jr], [van der] and [de la]
	player_name = re.sub(r"\s[Jj]r\s", " ", player_name)
	player_name = re.sub(r"\s[Vv]an\s[Dd]er\s", " ", player_name)
	player_name = re.sub(r"\s[Dd]e\s[Ll]a\s", " ", player_name)
	# remove all dashes
	player_name = re.sub(r"-", " ", player_name).strip()
	# do unidecode, make everything lower case, take only first 3 letters
	possible_surnames = [unidecode(w).lower()[:3] for w in player_name.split()]

	
	return possible_surnames


def create_match_ids(pl1, pl2, yr):

	"""
	IN:  player names; if singles, Sergio W. Chikkino and Hui T.; if doubles, then there's a "/" like in 
		Sergio W. Chikkino/Monika Broom and Hui T./Chung R.W.
	
	OUT: a list of strings representing possible match ids, e.g. ["chikkino_hui_broom_chung_2004"] 
	
	"""
	
	# if it's a singles (no "/" in player names)

	if "/" not in pl1:

		match_id_list = ["_".join(["_".join(sorted([sur1] + [sur2])), yr]) for sur1 in get_player_surnames(pl1) for sur2 in get_player_surnames(pl2)]
	
	else:

		# in this case, each "player" is like Cheung T./Pukkanen W. so we need to split by "/" 

		pair1_pl1, pair1_pl2 = pl1.split("/")
		pair2_pl1, pair2_pl2 = pl2.split("/")

		match_id_list = ["_".join(["_".join(sorted([sur1] + [sur2] + [sur3] + [sur4])), yr]) for sur1 in get_player_surnames(pair1_pl1) 
																								for sur2 in get_player_surnames(pair1_pl2)
																								for sur3 in get_player_surnames(pair2_pl1)
																								for sur4 in get_player_surnames(pair2_pl2)]

	return match_id_list

def create_id_list(df, years):

	lis = []

	for i in range(len(df.index)):
		# create lists of possible ids for every match and then put them in string separated with a comma
		lis.append(",".join(create_match_ids(df.player1[i], df.player2[i], years[i])))

	return lis


# date is either just a year or something like 2016-01-25
ao_years = ao_df.date.apply(lambda _: _ if "-" not in _ else _.split("-")[0]).tolist()
op_years = op_df.date.apply(lambda _: _.split()[-1]).tolist()
fs_years = fs_df.date.apply(lambda _: _.split("-")[0]).tolist()

ao_df["id"] = pd.Series(create_id_list(ao_df, ao_years)).values
op_df["id"] = pd.Series(create_id_list(op_df, op_years)).values
fs_df["id"] = pd.Series(create_id_list(fs_df, fs_years)).values

# create year columns
ao_df["year"] = pd.Series(ao_years).astype(int)
op_df["year"] = pd.Series(op_years).astype(int)
fs_df["year"] = pd.Series(fs_years).astype(int)

# merge the OddsPortal and FlashScore data; we only need year, time and id
compare_df = pd.concat([op_df.loc[:, ["year", "date", "time", "id"]], fs_df.loc[:, ["year", "date", "time", "id"]]])
compare_df =  compare_df.reset_index()
print("merged OddsPortal and FlashScore data contains {} rows...".format(len(compare_df.index)))

min_year_op = compare_df["year"].min()
max_year_op = compare_df["year"].max()

print("available years with starting times: {} to {}...".format(min_year_op, max_year_op))

# collect indices that weren't matched
nomatch_idx = []
nomatch_file = "nomatch.csv"

res_file = "ao_matches.csv"

starting_times = [None]*len(ao_df.index)
dates = [None]*len(ao_df.index)

# go back to possible ids as lists of strings
possible_ids = ao_df.id.str.split(",")
compare_ids = compare_df.id.str.split(",")

for i, ids_ao_match in enumerate(possible_ids):
	found_flag = 0
	for j, ids_other in enumerate(compare_ids):
		if set(ids_ao_match) & set(ids_other):
			found_flag = 1
			starting_times[i] = compare_df.loc[j, "time"]
			dates[i] = compare_df.loc[j, "date"]
			continue
	if found_flag == 0:
		for j, ids_other in enumerate(compare_ids):
			for v in ids_ao_match:
				for w in ids_other:
					if jellyfish.levenshtein_distance(v, w) < 2:
						found_flag = 1
						starting_times[i] = compare_df.loc[j, "time"]
						dates[i] = compare_df.loc[j, "date"]
						break
	if found_flag == 0:
		nomatch_idx.append(i)

total_matches_required = len(ao_df.index)
matched_ones = sum([s for s in map(lambda x: not (x is None), starting_times)])  # now many non-zeroes (i.e. successfully matched)
matched_pct = round(matched_ones*100/total_matches_required,1)

print("matched {}%".format(matched_pct))

ao_df["time"] = pd.Series(starting_times).values
ao_df["date"] = pd.Series(dates).values
ao_df = ao_df.drop("id",1)

ao_df.to_csv(res_file, index=False, sep="\t", columns=["round", "date", "time", "court", "player1", "player2"])
ao_df.iloc[nomatch_idx].to_csv(nomatch_file, index=False, sep="\t")
