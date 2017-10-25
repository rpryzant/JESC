"""
=== DESCRIPTION
This is a spellchecker that does dfs through the space of possible reconstructions, 
    with a combined bigram+unigram language model. 

=== USAGE
Make a `reconstructor` object, then use it however you want!

r = Reconstructor(corpus="leo-will.txt")
r.reconstruct("ehllo my name is Jack")     # ===> hello my name is Jack
"""
import collections
import math
import argparse
import sys
import heapq
import re
import time
import os
import random


class VowelInsertionProblem:
    def __init__(self, queryWords, bigramCost, possibleFills, dictionary):
        self.queryWords = queryWords
        self.bigramCost = bigramCost
        self.possibleFills = possibleFills
        self.dictionary = dictionary # all known correct spellings

    def startState(self):
         return wordsegUtil.SENTENCE_BEGIN, 0
 
    def isEnd(self, state):
         return state[1] == len(self.queryWords)
 
    def succAndCost(self, state):
        cur_word = self.queryWords[state[1]]
        fillings = self.possibleFills(cur_word)
        # corner case: there are no fillings - just return word as-is as the only successor
        if len(fillings) == 0 or self.dictionary[cur_word]:
            return [(cur_word, (cur_word, state[1] + 1), self.bigramCost(state[0], cur_word))]
        # else give all possible fillings as successors
        succ = []
        for filling in self.possibleFills(cur_word):
            succ.append((filling, (filling, state[1] + 1), self.bigramCost(state[0], filling)))
        return succ

 
class spellCheckUtil:
    @staticmethod
    def insertVowels(queryWords, bigramCost, possibleFills, dictionary):
         if len(queryWords) == 0:
            return ''

         ucs = UniformCostSearch(verbose=0)
         ucs.solve(VowelInsertionProblem(queryWords, bigramCost, possibleFills, dictionary))

         return ' '.join(ucs.actions) if ucs.actions else ""


class UniformCostSearch:
    def __init__(self, verbose=0):
        self.verbose = verbose

    def solve(self, problem):
        # If a path exists, set |actions| and |totalCost| accordingly.
        # Otherwise, leave them as None.
        self.actions = None
        self.totalCost = None
        self.numStatesExplored = 0

        # Initialize data structures
        frontier = PriorityQueue()  # Explored states are maintained by the frontier.
        backpointers = {}  # map state to (action, previous state)

        # Add the start state
        startState = problem.startState()
        frontier.update(startState, 0)

        while True:
            # Remove the state from the queue with the lowest pastCost
            # (priority).
            state, pastCost = frontier.removeMin()
            if state == None: break
            self.numStatesExplored += 1
            if self.verbose >= 2:
                print "Exploring %s with pastCost %s" % (state, pastCost)

            # Check if we've reached an end state; if so, extract solution.
            if problem.isEnd(state):
                self.actions = []
                while state != startState:
                    action, prevState = backpointers[state]
                    self.actions.append(action)
                    state = prevState
                self.actions.reverse()
                self.totalCost = pastCost
                if self.verbose >= 1:
                    print "numStatesExplored = %d" % self.numStatesExplored
                    print "totalCost = %s" % self.totalCost
                    print "actions = %s" % self.actions
                return

            # Expand from |state| to new successor states,
            # updating the frontier with each newState.
            for action, newState, cost in problem.succAndCost(state):
                if self.verbose >= 3:
                    print "  Action %s => %s with cost %s + %s" % (action, newState, pastCost, cost)
                if frontier.update(newState, pastCost + cost):
                    # Found better way to go to |newState|, update backpointer.
                    backpointers[newState] = (action, state)
        if self.verbose >= 1:
            print "No path found"


# Data structure for supporting uniform cost search.
class PriorityQueue:
    def  __init__(self):
        self.DONE = -100000
        self.heap = []
        self.priorities = {}  # Map from state to priority

    # Insert |state| into the heap with priority |newPriority| if
    # |state| isn't in the heap or |newPriority| is smaller than the existing
    # priority.
    # Return whether the priority queue was updated.
    def update(self, state, newPriority):
        oldPriority = self.priorities.get(state)
        if oldPriority == None or newPriority < oldPriority:
            self.priorities[state] = newPriority
            heapq.heappush(self.heap, (newPriority, state))
            return True
        return False

    # Returns (state with minimum priority, priority)
    # or (None, None) if the priority queue is empty.
    def removeMin(self):
        while len(self.heap) > 0:
            priority, state = heapq.heappop(self.heap)
            if self.priorities[state] == self.DONE: continue  # Outdated priority, skip
            self.priorities[state] = self.DONE
            return (state, priority)
        return (None, None) # Nothing left...


class wordsegUtil:
    SENTENCE_BEGIN = '-BEGIN-'
    @staticmethod
    def sliding(xs, windowSize):
        for i in xrange(1, len(xs) + 1):
            yield xs[max(0, i - windowSize):i]

    @staticmethod
    def removeAll(s, chars):
        return ''.join(filter(lambda c: c not in chars, s))

    @staticmethod
    def alphaOnly(s):
        s = s.replace('-', ' ')
        return filter(lambda c: c.isalpha() or c == ' ', s)

    @staticmethod
    def cleanLine(l):
        return wordsegUtil.alphaOnly(l.strip().lower())

    @staticmethod
    def words(l):
        return l.split()

    @staticmethod
    def editNeighbors(w):
        for i in range(len(w)):
            t = w[:]
            t = t[:i] + t[i+1:]
            yield t

    # Make an n-gram model of words in text from a corpus.
    @staticmethod
    def makeLanguageModels(path):
        unigramCounts = collections.Counter()
        totalCounts = 0
        bigramCounts = collections.Counter()
        bitotalCounts = collections.Counter()
        VOCAB_SIZE = 600000
        LONG_WORD_THRESHOLD = 5
        LENGTH_DISCOUNT = 0.15

        def bigramWindow(win):
            assert len(win) in [1, 2]
            if len(win) == 1:
                return ('-BEGIN-', win[0])
            else:
                return tuple(win)

        with open(path, 'r') as f:
            for l in f:
                ws = wordsegUtil.words(wordsegUtil.cleanLine(l))
                unigrams = [x[0] for x in wordsegUtil.sliding(ws, 1)]
                bigrams = [bigramWindow(x) for x in wordsegUtil.sliding(ws, 2)]
                totalCounts += len(unigrams)
                unigramCounts.update(unigrams)
                bigramCounts.update(bigrams)
                bitotalCounts.update([x[0] for x in bigrams])

        def unigramCost(x):
            if x not in unigramCounts:
                length = max(LONG_WORD_THRESHOLD, len(x))
                return -(length * math.log(LENGTH_DISCOUNT) + math.log(1.0) - math.log(VOCAB_SIZE))
            else:
                return math.log(totalCounts) - math.log(unigramCounts[x])

        def bigramModel(a, b):
            return math.log(bitotalCounts[a] + VOCAB_SIZE) - math.log(bigramCounts[(a, b)] + 1)

        return unigramCost, bigramModel

    @staticmethod
    def logSumExp(x, y):
        lo = min(x, y)
        hi = max(x, y)
        return math.log(1.0 + math.exp(lo - hi)) + hi;

    @staticmethod
    def smoothUnigramAndBigram(unigramCost, bigramModel, a):
        '''Coefficient `a` is Bernoulli weight favoring unigram'''

        # Want: -log( a * exp(-u) + (1-a) * exp(-b) )
        #     = -log( exp(log(a) - u) + exp(log(1-a) - b) )
        #     = -logSumExp( log(a) - u, log(1-a) - b )

        def smoothModel(w1, w2):
            u = unigramCost(w2)
            b = bigramModel(w1, w2)
            return -logSumExp(math.log(a) - u, math.log(1-a) - b)

        return smoothModel

    # Make a map for inverse lookup of words missing chars ->
    # full words
    @staticmethod
    def makeInverseRemovalDictionary(path):
        wordsRemovedToFull = collections.defaultdict(set)
        dictionary = collections.defaultdict(lambda: False)

        with open(path, 'r') as f:
            for l in f:
                for w in wordsegUtil.words(wordsegUtil.cleanLine(l)):
                    dictionary[w] = True
                    for wp in wordsegUtil.editNeighbors(w):    # all edit distance 1 candidates
                        wordsRemovedToFull[wp].add(w)

        wordsRemovedToFull = dict(wordsRemovedToFull)
        empty = set()

        def possibleFills(short):
            return wordsRemovedToFull.get(short, empty)

        return possibleFills, dictionary


class Reconstructor:
    def __init__(self, corpus=None):
        corpus = corpus or 'leo-will.txt'
    
        self.unigramCost, self.bigramCost = wordsegUtil.makeLanguageModels(corpus)
        self.possibleFills, self.dictionary = wordsegUtil.makeInverseRemovalDictionary(corpus)
        
    def reconstruct(self, s):
        """ reconstruct a sentance s 
        """
        s = wordsegUtil.cleanLine(s)
        ws = [w for w in wordsegUtil.words(s)]
        return spellCheckUtil.insertVowels(ws, self.bigramCost, self.possibleFills, self.dictionary)


class Shell:
    def main(self):
        args = self.parseArgs()
        if args.model and args.model not in ['seg', 'ins', 'both']:
            print 'Unrecognized model:', args.model
            sys.exit(1)

        corpus = args.text_corpus or 'leo-will.txt'

        sys.stdout.write('Training language cost functions [corpus: %s]... ' % corpus)
        sys.stdout.flush()

        unigramCost, bigramCost = wordsegUtil.makeLanguageModels(corpus)
        possibleFills, dictionary = wordsegUtil.makeInverseRemovalDictionary(corpus)

        print 'Done!'
        print ''

        self.repl(unigramCost, bigramCost, possibleFills, dictionary, command=args.model)


    def parseArgs(self):
        p = argparse.ArgumentParser()
        p.add_argument('--text-corpus', help='Text training corpus')
        p.add_argument('--model', help='Always use this model')
        return p.parse_args()


    # REPL and main entry point
    def repl(self, unigramCost, bigramCost, possibleFills, dictionary, command=None):
        '''REPL: read, evaluate, print, loop'''
        while True:
            sys.stdout.write('>> ')
            line = sys.stdin.readline().strip()
            if not line:
                break

            if command is None:
                cmdAndLine = line.split(None, 1)
                cmd, line = cmdAndLine[0], ' '.join(cmdAndLine[1:])
            else:
                cmd = command
                line = line

            print ''

            if cmd == 'ins':
                line = wordsegUtil.cleanLine(line)
    #            ws = [wordsegUtil.removeAll(w, 'aeiou') for w in wordsegUtil.words(line)]
                ws = [w for w in wordsegUtil.words(line)]
                print '  Query (ins):', ' '.join(ws)
                print ''
                print '  ' + spellCheckUtil.insertVowels(ws, bigramCost, possibleFills, dictionary)

            else:
                print 'Unrecognized command:', cmd

            print ''

if __name__ == '__main__':
    shell = Shell()
    shell.main()
