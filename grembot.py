#!/usr/bin/env python

import os
import re
import sys
import json
import time
import logging
import random
import buffer
import markov.markov
import irc.client

config = None;
markov_bot = None;
command_map = dict()
colour_regex = re.compile("\x03(?:\d{1,2}(?:,\d{1,2})?)?", re.UNICODE)
time_since_last_save = time.time()

def load_config(config_name):
	global config
	with open(config_name, "r") as c:
		config = json.load(c)

def on_connect(connection, event):
	global config
	for c in config["channels"]:
		connection.join(c)

def on_join(connection, event):
	print("Joined " + event.target)
	#connection.privmsg(event.target, "test")

def on_info_cmd(bot, event, data):
	return bot.GetInfo()

def on_save_cmd(bot, event, data):
	from_nick = extract_nick(event.source)
	if from_nick in config["admins"]:
		bot.SaveLines()
		return "Saved Data"
	else:
		return "Unauthorized"

def on_getcontexts_cmd(bot, event, data):
	try:
		if event.type == "privmsg":
			reply = ""
			for c in bot.GetContextsForWord(data[1]):
				reply.append("[{0}] ".format(c))

			return reply
		else:
			return "Only available from private message."
	except:
		return "No word given or whatever."


def on_message(connection, event):
	global markov_bot;
	global time_since_last_save;
	sender = event.source
	target = event.target
	message = event.arguments[0]

	bot_nickname = config["nick"]

	if(bot_nickname == target): return

	message = message.encode('utf-8')
	bot_nickname = bot_nickname.encode('utf-8')
	
	# strip annoying IRC colours
	message = colour_regex.sub("", message)

	print "[{0}] {1}: {2}".format(target, extract_nick(sender), message)

	# determine if we are even being talked to
	send_reply = False
	if bot_nickname in message or event.type == "privmsg":
		send_reply = True

	# filter out possible quote / name variations
	name_vars = get_name_variations(bot_nickname)
	for v in name_vars:
		message = message.replace(v, "")

	# remove leading whitespace after name strip
	message = message.lstrip()

	#print "Stripped message: {0}".format(message)

	was_command = False
	if send_reply:
		if len(message) > 0:
			# handle "commands"
			if message[0] == "!":
				was_command = True
				tokens = message[1:].split()
				reply = ""
				if(tokens[0] in command_map):
					reply = command_map[tokens[0]](markov_bot, event, tokens)
				else:
					reply = "Unknown Command: {0}".format(tokens[0])

				if reply:
					connection.privmsg(target, "{0}: {1}".format(extract_nick(sender), reply))

			# otherwise get a bot reply
			else:
				reply = markov_bot.GetReply(message).encode('ascii', 'ignore')
				if reply:
					connection.privmsg(target, reply)
					print "({0}) -> [{1}]: {2}".format(bot_nickname, target, reply)

	if not was_command:
		markov_bot.LearnLine(message)

	# check when we last saved
	if (time.time() - time_since_last_save) >= config["save_interval"]:
		markov_bot.SaveLines()
		time_since_last_save = time.time()



def get_name_variations(name):
	# start char, end char
	possible_tokens = [ ["", ","], ["", ":"], ["[", "]:"], ["[", "]"], ["<", ">:"], ["<", ">"], ["", ""] ]
	variations = []
	for t in possible_tokens:
		variation = "{0}{1}{2}".format(t[0], name, t[1])
		variations.append(variation.encode('utf-8'))

	return variations

def extract_nick(hostmask):
	tokens = hostmask.split("!")
	if len(tokens) > 0:
		return tokens[0]

	return ""

def main():
	global config
	global markov_bot
	load_config("config.json")

	#irc.client.ServerConnection.buffer_class = irc.client.LineBuffer

	client = irc.client.IRC()
	#client.server().buffer_class = buffer.UTF16LineBuffer

	markov_bot = markov.markov.MarkovBot(config["lines_file"], config["min_context_depth"], config["max_context_depth"])

	try:
		print "Connecting to {0}:{1} with Nick {2}".format(config["server"], config["port"], config["nick"])
		c = client.server().connect(config["server"], config["port"], config["nick"])
	except irc.client.ServerConnectionError:
		print(sys.exc_info()[1])
		raise SystemExit(1)

	c.add_global_handler("welcome", on_connect)
	c.add_global_handler("join", on_join)
	c.add_global_handler("pubmsg", on_message)
	c.add_global_handler("privmsg", on_message)

	command_map["info"] = on_info_cmd;
	command_map["save"] = on_save_cmd;
	command_map["getcontexts"] = on_getcontexts_cmd

	client.process_forever()

if __name__ == "__main__":
	main()
