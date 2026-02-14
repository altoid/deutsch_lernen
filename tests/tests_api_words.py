# test cases for api_words.get_words.
#
# wordlist_ids but no tags
# - get all the words in the wordlists.  must work for smart lists.
#
# tags but no wordlist_ids
# - every word with any of the tags in any of the wordlists.  for smart lists this is a no-op.
#
# tags and wordlist ids both
# - get every word in all the wordlists that has the given tags.  for smart lists this is a no-op.
#
# neither
# - this case will fetch the whole dictionary.
#
# the endpoint has to work for smart lists.
#
