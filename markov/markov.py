import os
import re
import random
from collections import deque

class MarkovBot(object):
	def __init__(self, _lines_file, _min_context_depth, _max_context_depth):
		self.lines_file = _lines_file
		self.min_context_depth = _min_context_depth;
		self.max_context_depth = _max_context_depth;

		self.lines = []
		self.contexts = dict()
		self.num_contexts = 0
		self.num_lines = 0

		self.LoadLines()

	def LoadLines(self):
		print "Loading lines from {0}".format(self.lines_file)
		if os.path.exists(self.lines_file):
			with open(self.lines_file, "r") as f:
				for l in f:
					self.LearnLine(l)

		print self.GetInfo()

	def SaveLines(self):
		print "Saving Lines"
		with open(self.lines_file, "w") as f:
			for l in self.lines:
				f.write("{0}\n".format(l))

		print "Saved"

		
	def GetInfo(self):
		num_words = len(self.contexts)
		avg_words = 0
		if self.num_contexts > 0 and num_words > 0:
			avg_words = self.num_contexts / num_words

		return "I know {0} words in {1} contexts with avg {2} contexts per word.".format(num_words, self.num_contexts, avg_words)

	def GetContextsForWord(self, word):
		lines = []
		contexts = self.contexts[word.lower()]

		for c in contexts:
			lines.append(self.lines[c[0]])

		return lines


	def LearnLine(self, line):
		if line:
			sentences = line.split(". ")

			for l in sentences:
				clean_line = ' '.join(l.split(" "))

				self.lines.append(clean_line)
				line_index = self.num_lines
				self.num_lines += 1

				tokens = self.TokenizeString(clean_line.lower())

				# ignore single word lines for learning
				if len(tokens) > 1:
					token_count = 0
					for t in tokens:
						if t not in self.contexts:
							self.contexts[t] = []

						context = line_index, token_count
						self.contexts[t].append(context)
						self.num_contexts += 1
						token_count += 1

	def GetReply(self, message):
		reply = ""
		sentence = deque()
		tokens = self.TokenizeString(message)

		available_words = []
		for t in tokens:
			if t.lower() in self.contexts:
				available_words.append(t)

		if len(available_words) > 0:
			# pick a random word
			word = available_words[random.randint(0, len(available_words) - 1)]
			sentence.append(word)

			
			# build left edge
			done = False
			while not done:

				# get contexts
				contexts = self.contexts[word.lower()]

				# get random context
				rand_context = contexts[random.randint(0, len(contexts) - 1)]
				w = rand_context[1]
				line = self.lines[rand_context[0]]

				words = self.TokenizeString(line)

				# get a random depth
				depth = random.randint(self.min_context_depth, self.max_context_depth)

				for i in range(1, depth):
					if (w - i) < 0:
						done = True
						break
					else:
						sentence.appendleft(words[w - i])

					if (w - i) is 0:
						done = True
						break


			# build the right hand side
			done = False
			while not done:
				end_of_sentence = len(sentence) - 1

				# get contexts
				contexts = self.contexts[sentence[end_of_sentence].lower()]

				# get random context
				rand_context = contexts[random.randint(0, len(contexts) - 1)]
				w = rand_context[1]
				line = self.lines[rand_context[0]]

				words = self.TokenizeString(line)
				num_words = len(words)

				# get a random depth
				depth = random.randint(self.min_context_depth, self.max_context_depth)

				for i in range(1, depth):
					if (w + i) >= num_words:
						done = True
						break
					else:
						sentence.append(words[w + i])


			#context_line_ix = contexts[random.randint(0, len(contexts) - 1)][0]
			#reply = self.lines[context_line_ix]

			reply = ' '.join(sentence)

		return reply


	def TokenizeString(self, text):
		return text.split()
		#return re.findall(r"[\w']+", text)

