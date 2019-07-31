import math,time
import re
from multiprocessing import Pool
from utils.wildcards import generate_patterns, permutation_pattern

def convert_array_string_to_int(array):
    binaryArray = [int(element) for element in array]
    return binaryArray

def top_similarity_degree(hashElement,numberOfBits):
    top = 0
    arrayDegree = [0 for i in range(0,numberOfBits)]

    for key in hashElement.keys():
        degree = 0
        arrayChar = list(key)
        for i in range(0,len(arrayChar)):
            if arrayChar[i] == "1":
                arrayChar[i] = "0"
            else:
                arrayChar[i] = "1"
            keyToCheck = ''.join(arrayChar)
            if keyToCheck in hashElement:
                degree+=1
            arrayChar = list(key)
        arrayDegree[degree-1]+=1
        hashElement[key]["maxBitsSimilarity"]=degree
        if degree>top:
            top=degree

    valid = False
    max=top

    while (not valid) and (max>0):
        sum=0
        for i in range(top-1,max-1,-1):
            sum+=arrayDegree[i]
        if math.pow(2,max)<=sum:
            valid=True
            break
        max-=1
    if (not valid) and (max>0):
        max=top-1

    return max

def wild_card_search(binaryWild, hashElement, maxWild, solution):

    countWildCards = binaryWild.count(2)

    if countWildCards < maxWild:
        return False

    provisorySolution = permutation_pattern(binaryWild,maxWild)

    #DEFAULT IMPLEMENTATION
    setHashElement = set(hashElement)
    print "Number Combinations: " + str(len(provisorySolution))
    has_validSolution = False
    for arr in provisorySolution:
        setListBinaries = set(generate_patterns(arr))
        if len(setListBinaries - setHashElement) == 0:
            solution.append(arr)
            has_validSolution = True
            for element in setListBinaries:
                if element in hashElement:
                    del hashElement[element]
    print "Done!"



    # print "Number Combinations: " + str(len(provisorySolution))
    # has_validSolution = False
    # requiredEntries = int(math.pow(2, maxWild))
    # partial_solution = []
    # for arr in provisorySolution:
    #     pattern = '^' + arr.replace('2','[01]') + '?'
    #     totalMatches = sum(re.match(pattern,candidate) is not None for candidate in hashElement)
    #     print("entrou")
    #     if totalMatches == requiredEntries:
    #         solution.append(arr)
    #         partial_solution.append(pattern)
    #         has_validSolution = True
    # print "Partial!"
    # for pattern in partial_solution:
    #     discard_elements = []
    #     for candidate in hashElement:
    #         if re.match(pattern, candidate) is not None:
    #             discard_elements.append(candidate)
    #     for element in discard_elements:
    #         del hashElement[element]
    #     if len(hashElement) == 0:
    #         break
    # print "Done!"






    # hashPotentialSolution = {arr:genvagran erate_patterns(arr) for arr in provisorySolution}
    #
    # print "Entrou 1.4"
    #
    # has_validSolution = False
    # for key in hashPotentialSolution.keys():
    #     setListBinaries = set(hashPotentialSolution.get(key))
    #     if len(setListBinaries-setHashElement) == 0:
    #         solution.append(key)
    #         has_validSolution = True
    #
    # print "Entrou 1.5"
    #
    # for key in solution:
    #     if key in hashPotentialSolution:
    #         listBinaries = hashPotentialSolution.get(key)
    #         for element in listBinaries:
    #             key2 = element
    #             if key2 in hashElement:
    #                 del hashElement[key2]
    #
    # print "Entrou 1.6"

    return has_validSolution

def generate_values_with_wildcards(bin_list, size):

    numberOfBits = size
    solution = []

    hashBinaryElement = {}
    for value in bin_list:
        hashBinaryElement[value] = {"binaryString":value,"binaryIntArray":convert_array_string_to_int(value),"maxBitsSimilarity":0,
         "amountOfSimilarity":0,"arraySimilarity":[0 for i in range(0,numberOfBits)]}

    maxWildCard = top_similarity_degree(hashBinaryElement,numberOfBits)

    while len(hashBinaryElement) > 0:

        arraySum0 = [0 for i in range(0,numberOfBits)]
        arraySum1 = [0 for i in range(0,numberOfBits)]

        geralAmountOfWildcard=int(math.log(len(hashBinaryElement),2))
        if geralAmountOfWildcard<maxWildCard:
            maxWildCard=geralAmountOfWildcard
            print("maxWildCard Alterado")

        for key in hashBinaryElement.keys():
            if hashBinaryElement[key]["maxBitsSimilarity"]>=maxWildCard:
                binaryArray = hashBinaryElement[key]["binaryIntArray"]
                for index in range(0, len(binaryArray)):
                    if binaryArray[index] == 0:
                        arraySum0[index] += 1
                    else:
                        arraySum1[index] += 1

        #groupAmoutOfWildcard = int(math.log(countGroupWildcard,2))
        requiredEntries = int(math.pow(2,maxWildCard)/2)
        wildCardTest = [2 for i in range(0,numberOfBits)]

        for index in range(0,numberOfBits):
            if arraySum0[index] == 0:
                wildCardTest[index] = 1
            elif arraySum1[index] == 0:
                wildCardTest[index] = 0
            elif (arraySum1[index] > requiredEntries) and (arraySum0[index] < requiredEntries):
                wildCardTest[index] = 1
            elif (arraySum0[index] > requiredEntries) and (arraySum1[index] < requiredEntries):
                wildCardTest[index] = 0

        #print(arraySum0)
        #print(arraySum1)

        print("Number Elements: " + str(len(hashBinaryElement))
              + " maxWildCard: " + str(maxWildCard)
              + " requiredEntries: " + str(requiredEntries)
              + " pattern: " + str(wildCardTest))

        vSolution = wild_card_search(wildCardTest, hashBinaryElement, maxWildCard, solution)

        #print("vSolution: " + str(vSolution))

        maxWildCard -= 1

        if vSolution:
            aux = top_similarity_degree(hashBinaryElement,numberOfBits)
            if aux<maxWildCard:
                maxWildCard=aux

    return [s.replace("2", "*") for s in solution]

