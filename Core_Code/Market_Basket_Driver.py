'''
@author:    Driver method by Matt Raymond, original code by Trevor Kling
@desc:      This file contains a driver method for our apriori algorithm, and is
            meant to simplify implimentation in future code
'''

import Main_Model
import os
import json
from apyori import apriori
import re # might be able to remove
from Loading_Bar import Loading_Bar as lb
from time import time
import datetime

'''
DESC:   Loads all of the photo data from the given directory and returns it in
        a dictionary

INPUT:  sourceDir:str = "../Data/Scan_Result"
            - Where the jsons of photo data will be found
        verbose:bool = False
            - Whether the function will output a status of what it's doing

OUTPUT: Returns a dictionary where the keys are photo names and the values are
        lists of astronauts in the photo
'''
def loadPhotos(sourceDir:str = '../Data/Scan_Result', verbose:bool = False):
    photos = {}

    # Get all json files in the directory
    files = [f for f in os.listdir(sourceDir) if ".json" in f]

    #  If there are no json files
    if verbose and not files:
        print("\tNone")
        return {}

    if verbose: bar = lb(len(files), message='Loading files')

    # Cycle through all json files
    for file in files:
        # Find the partially-qualified filepath
        fp = sourceDir + "/" + file
        # Open file and read data
        with open(fp) as jsonfile:
            data = json.load(jsonfile)

            # Break up by photo and add to photos dictionary
            for k in data.keys():
                photos[k] = data[k]
                # if verbose:
                #     print("\t" + k)

        if verbose: bar.update()
    if verbose: bar.update(True)

    return photos


'''
DESC:   Gets lists of astronauts in each photo

INPUT:  photos:dict
            - A dictionary of photo data

OUTPUT: A list of lists, where each inner list is a list of astronauts in each
        photo
'''
def generateTransactions(photos:dict, verbose:bool = False):
    if verbose: bar = lb(len(photos.keys()), message='Generating transactions')

    transactions = []
    # Cycles through all of the photos
    for k in photos.keys():
        # if verbose: print('\t{0}'.format(k))
        # Grabs the lists of astronauts in each photo
        transactions += [[k2 for k2 in list] for list in photos[k]]
        if verbose: bar.update()

    if verbose: bar.update(True)
    return transactions


'''
DESC:   Removes all the transactions which do not contain any astronaut names

INPUT:  transactions:list
            - A list of lists, where each inner list is a list of astronauts in
            each photo

OUTPUT: A list in the same format as the input, but with no empty sub-lists
'''
def cleanTransactions(transactions:list, verbose:bool = False):
    if verbose: bar = lb(len(transactions), message='Cleaning transactions')

    finalTransactions = []
    for i in transactions:
        # if verbose: print('\t{0}'.format(i))
        if len(i) > 0: finalTransactions.append(i)
        if verbose: bar.update()

    if verbose: bar.update(True)
    return finalTransactions


'''
DESC:   Applies an apriori Market Basket Analysis algorithm to find the most
        frequent pairs. The minsupport is set to a very low value, as only a few
        of the photos will contain any specific astronaut. We then use a very
        high min confidence, to ensure the model is quite sure the relationship
        is correct.

INPUT:  transactions:list
            - A list of lists, where each inner list is a list of astronauts in
            each photo

OUTPUT: A dictionary that contains all of the apriori data
'''
def runApriori(transactions:list, verbose:bool = False, threshold = 6):
    if verbose:
        # Created by graphing times in excel and using logarithmic trendline
        prediction = 0.000873*(2.71828**(1.93*threshold))
        h = int(prediction // 3600)
        m = int(prediction // 60)
        s = int(prediction % 60)
        startingTime = datetime.datetime.now()
        endingTime = startingTime + datetime.timedelta(0,prediction)

        print('Running apriori algorithm. We estimate this should take {0} hours, {1} minutes, and {2} seconds to complete.'.format(h,m,s))
        print("You started at {0}, so the algorithm should finish at {1}.".format(startingTime.strftime("%I:%M %p"), endingTime.strftime("%I:%M %p")))



    return list(apriori(transactions, min_support=0.01, min_confidence=0.80,
        min_lift=1.0, max_length=threshold))


'''
DESC:   Parse the information out of the apriori results

INPUT:  results:list
            - The results from the apriori algorithm
        save:bool = False
            - Whether the data should be saved in a file
        fileName:str = "../Data/frequentPairs"
            - The filepath for the data to be saved in. Should not contain a
            file extension

OUTPUT: Returns a dictionary of frequent pairs/items
'''
def findFrequentItems(results:list, save:bool = False, fileName:str = "../Data/frequentPairs", verbose:bool = False):
    if verbose: bar = lb(len(results), message='Finding frequent items')


    frequentItems = {}
    for r in results:
        # Pull out names of each astronaut in a pair
        names = [x for x in r[0]]
        pair = str((names[0], names[1]))

        # If the pair isn't in the results, add them and their information
        if pair not in results:
            frequentItems[pair] = {}
            frequentItems[pair]["support"] = r[1]
            frequentItems[pair]["confidence"] = r[2][0][2]
            frequentItems[pair]["lift"] = r[2][0][3]

        # If there's a higher confidence level somewhere, replace the values
        # with that one
        elif r[2][0][2] > results[pair]["confidence"]:
            frequentItems[pair]["support"] = r[1]
            frequentItems[pair]["confidence"] = r[2][0][2]
            frequentItems[pair]["lift"] = r[2][0][3]
        if verbose: bar.update()
    if verbose: bar.update(True)

    if save:
        if verbose: print('Saving result')
        # Save the frequent pairs data to a json
        with open('{0}.json'.format(fileName), 'w') as fp:
            json.dump(frequentItems, fp)

    return frequentItems


'''
DESC:   Find the raw freqencies at which astronauts are found

INPUT:  photos:dict
            - A dictionary of photos that has been loaded in
        save:bool = False
            - Whether the result should be saved to a json file
        fileName:str = "../Data/rawFrequencies"
            - The filename of the file that the results will be saved in

OUTPUT: A dictionary where keys are astronaut names and values are the
        frequencies that they are found in
'''
def findRawFrequencies(photos:dict, save:bool = False, fileName:str = "../Data/rawFrequencies", verbose:bool = False):
    if verbose: bar = lb(len(photos.values()), message='Finding raw frequencies')

    frequencies = {}
    for astros in photos.values():
        for astro in astros[0].keys():
            # If the astro is not in the dictionary, add them
            if astro not in frequencies:
                frequencies[astro] = 1
            # If they are, add one to their frequency
            else:
                frequencies[astro] += 1
        if verbose: bar.update()
    if verbose: bar.update(True)
    if save:
        if verbose: print('Saving result')

        # Save the frequencies at which pairs appear to a json
        with open('{0}.json'.format(fileName), 'w') as fp:
            json.dump(frequencies, fp)

    return frequencies


'''
DESC:   Produce a dictionary of all pairs appearing in the photos

INPUT:  photos:dict
            - A dictionary of photos that has been loaded in
        save:bool = False
            - Whether the result should be saved to a json file
        fileName:str = "pairs"
            - The filename of the file that the results will be saved in

OUTPUT: A dictionary where keys are tuples of astronaut name pairings and the
        values are the number of times that they were in photos together
'''
def findPairs(photos:dict, save:bool = False, fileName:str = "../Data/pairs", verbose:bool = False):
    if verbose: bar = lb(len(photos), message='Finding pairs')

    pairs = {}
    for photo in photos:
        for a1 in range(0, len(photo)):
            for a2 in range(a1, len(photo)):
                # Skip when they're the same astronaut
                if photo[a1] == photo[a2]:
                    continue

                if str((photo[a1], photo[a2])) in pairs:
                    pairs[str((photo[a1], photo[a2]))] += 1
                elif str((photo[a2], photo[a1])) in pairs:
                    pairs[str((photo[a2], photo[a1]))] += 1
                else:
                    pairs[str((photo[a1], photo[a2]))] = 1

        if verbose: bar.update()
    if verbose: bar.update(True)

    if save:
        if verbose: print('Saving result')

        # Save the frequencies at which pairs appear to a json
        with open('{0}.json'.format(fileName), 'w') as fp:
            json.dump(pairs, fp)

    return pairs


'''
DESC:   Runs the entire model and returns the results

INPUT:  apriori:bool = False
            - Whether the apriori algorithm should be run and return a value
        fItems:bool = False
            - Whether the frequent items from the apriori algorithm should be
            returned
        rawF:bool = False,
            - Whether the raw frequencies of astronauts should be found and
            returned
        sourceDir:str = '../Data/Scan_Result'
            - Where the photo data was saved in json format. Will only go one
            directory deep (will not search sub-directories)
        verbose:bool = False
            - Whether the program should output information on what it's doing
        saveFreq:bool = False,
            - Whether the frequent items data should be saved
        freqFileName:str = "frequentPairs"
            - Where the frequent items data should be saved
        saveRawFreq:bool = False,
            - Whether the raw frequencies data should be saved
        rawFreqFileName:str = "rawFrequencies"
            - Where the raw frequencies data should be saved
        savePairs:bool = False,
            - Whether the astronaut pairing data should be saved
        pairFileName:str = "pairs"
            - Where the astronaut pairing data should be saved

OUTPUT: A dictionary that contains the information specified by the boolean
        parameters
'''
def runModel(apriori:bool = False, fItems:bool = False, rawF:bool = False,
    pairs:bool = False, sourceDir:str = '../Data/Scan_Result', verbose:bool = False,
    saveFreq:bool = False, freqFileName:str = "../Data/frequentPairs",
    saveRawFreq:bool = False, rawFreqFileName:str = "../Data/rawFrequencies",
    savePairs:bool = False, pairFileName:str = "../Data/pairs"):

    # Skips the entire thing if the flags indicate nothing should be run
    if not (apriori or fItems or rawF or pairs): return {}

    returnValue = {}
    photos = loadPhotos(sourceDir, verbose)
    transactions = generateTransactions(photos, verbose)
    transactions = cleanTransactions(transactions, verbose)

    if apriori or fItems:
        results = runApriori(transactions, verbose)
        if fItems:
            returnValue["frequentItems"] = findFrequentItems(results, saveFreq, freqFileName, verbose)
        if apriori:
            returnValue["apriori"] = results

    if rawF:
        returnValue["rawFreq"] = findRawFrequencies(photos, saveRawFreq, rawFreqFileName, verbose)

    if pairs:
        returnValue['pairs'] = findPairs(transactions, savePairs, pairFileName, verbose)

    return returnValue



if __name__ == "__main__":
    result = runModel(apriori = True, fItems = True, rawF = True, pairs = True, verbose = True,
        saveFreq = True, saveRawFreq = True, savePairs = True, sourceDir = "../Data/Scan_Result/")

    # print(result)
