import math
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
    has_validSolution = False
    for arr in provisorySolution:
        setListBinaries = set(generate_patterns(arr))
        if len(setListBinaries - setHashElement) == 0:
            solution.append(arr)
            has_validSolution = True
            for element in setListBinaries:
                if element in hashElement:
                    del hashElement[element]

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

        vSolution = wild_card_search(wildCardTest, hashBinaryElement, maxWildCard, solution)
        maxWildCard -= 1

        if vSolution:
            aux = top_similarity_degree(hashBinaryElement,numberOfBits)
            if aux<maxWildCard:
                maxWildCard=aux

    return [s.replace("2", "*") for s in solution]

