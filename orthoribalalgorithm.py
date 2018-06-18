# orthoribalalgorithm.py
# Rice University iGEM 2018

# ---------------------------------------Step 1----------------------------------------------------------
def convertTtoU(sequence):
    # Convert thymine to uracil
    return sequence.replace('T', 'U')


def revcomp(sequence):
    # give reverse complementary sequence
    complement = {"A": "U", "U": "A", "C": "G", "G": "C", "N": "N"}
    revcompseq = ""
    sequence_list = list(sequence)
    sequence_list.reverse()
    for letter in sequence_list:
        revcompseq += complement[letter.upper()]
    return revcompseq


def SDseqnum2str(code):
    # Translate a 6-digit number to its responding 6-base SD sequence
    seq = ''
    codex = 'AUCG'
    for i in range(0, len(code)):
        index = int(code[i])
        seq = seq + codex[index-1]
    return seq


def ASDseqnum2str(code):
    # Translate a 6-digit number to its responding 12-base ASD sequence
    seq = revcomp(SDseqnum2str(code))
    seq = 'AUCA' + seq + 'UA'
    return seq


def libbuild():
    # Build a library of 4096 pairs
    Lib = []
    for b1 in range(1,5):
        for b2 in range(1,5):
            for b3 in range(1,5):
                for b4 in range(1,5):
                    for b5 in range(1,5):
                        for b6 in range(1,5):
                            seqcode = str(b1) + str(b2) + str(b3) + str(b4) + str(b5) + str(b6)
                            SDseq = SDseqnum2str(seqcode)
                            ASDseq = ASDseqnum2str(seqcode)
                            Lib.append([SDseq, ASDseq])
    Libdict = {}
    for x in range(0,4096):
        pair = Lib[x]
        Libdict['SD{0}'.format(x+1)] = pair[0]
        Libdict['ASD{0}'.format(x+1)] = pair[1]
    print('4096 pairs are: ', Libdict)
    return Libdict

# ------------------------------------------Step 2---------------------------------------------------------------


def RNAduplexval(ASD,SD):
    # call RNAduplex in python shell, ***change RNAduplex path used below corresponding to position of RNAduplex.exe***
    import subprocess
    input = ASD + '\n' + SD + '\n'
    input = input.encode('utf-8')
    from subprocess import Popen,PIPE,STDOUT
    result = Popen(["C:\\Users\\siddu\\Desktop\\Python Code\\Vienna\\RNAduplex"], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    m = result.communicate(input=input)[0]
    val = m.decode('utf-8')
    n = val.find(':')
    val = val[n+11:-3]
    return val

# -----------------------------------------Step 3----------------------------------------------------------------


def updatelibindex(Library):
    # update the index of the sequence in the library to be continuous
    liblen = len(Library) / 2
    n = 1
    while (n < liblen + 1):
        testidx = n
        while 'ASD' + str(testidx) not in Library:
            testidx = testidx + 1
        Library['ASD{0}'.format(n)] = Library.pop('ASD{0}'.format(testidx))
        Library['SD{0}'.format(n)] = Library.pop('SD{0}'.format(testidx))
        n = n + 1
    return Library


def narrow_binding(WtASD,WtSD):
    # Input the wildtype ASD and SD, output is the narrowed library with pairs that fall within 0.5 kcal range of the
    #  wildtype binding energy
    Wildval = RNAduplexval(WtASD,WtSD)
    SequenceLib = libbuild()
    for n in range(0,4096):
        ASD = SequenceLib['ASD'+str(n+1)]
        SD = SequenceLib['SD' + str(n+1)]
        val = RNAduplexval(ASD,SD)
        if float(Wildval) - 0.5 >= float(val) or float(val) >= float(Wildval) + 0.5:
            del SequenceLib['ASD'+str(n+1)]
            del SequenceLib['SD'+str(n+1)]
    Libdict = updatelibindex(SequenceLib)
    return Libdict

#---------------------------Step 4-------------------------------------------------------------------


def RNAfoldseq(fullRNAsequence):
    # call RNAfold program in python, ***change full path of program accordingly
    import subprocess
    input = fullRNAsequence
    input = input.encode('utf-8')
    from subprocess import Popen,PIPE,STDOUT
    result = Popen(["C:\\Users\\siddu\\Desktop\\Python Code\\Vienna\\RNAfold"], stdout=subprocess.PIPE,stdin=subprocess.PIPE)
    m = result.communicate(input=input)[0]
    val = m.decode('utf-8')
    val = val[len(fullRNAsequence)+1:len(fullRNAsequence)*2+1]
    return val
#-------------------------------Step 5--------------------------


def secstructurelib(Library,full16srRNAseq):
    # Build a library of secondary structure of 16s rRNA corresponding to a given library of ASD and SD sequence.
    NewLib = {}
    for n in range(0,int(len(Library)/2)):
        full16srRNAseq = full16srRNAseq[0:-12] + Library['ASD{0}'.format(n+1)]
        secstructure = RNAfoldseq(full16srRNAseq)
        NewLib['foldedseq{0}'.format(n+1)] = str(secstructure)
    return NewLib


def ASD_2rystructure_narrow(full16srRNAseq):
    # Narrow down the library by discarding sequences that forms secondary structure in ASD region
    # Import the most narrowed Libdict up to step 5 as well as the secondary structure dictionary.
    WtASD = full16srRNAseq[-12:-1] + full16srRNAseq[-1]
    WtSD = revcomp(WtASD[4:10])
    Library = narrow_binding(WtASD, WtSD)
    print('Library after step 2: ', Library)
    secstructureseqlib = secstructurelib(Library, full16srRNAseq)
    # Locate the index of the first bp of the ASD for all 16S rRNA sequences
    import re
    for pseudoindex in re.finditer('AUCA', full16srRNAseq):
        if full16srRNAseq[pseudoindex.start() + 10:pseudoindex.start() + 12] == 'UA':
            index = int(pseudoindex.start())
    """Iterate through the whole secondary structure dictionary, locating a constant positioned
    ASD and determining whether there is secondary structure in that ASD"""
    for i in range(0, int(len(Library)/2)):
        secname = "foldedseq" + str(i + 1)
        ASDname = "ASD" + str(i + 1)
        SDname = "SD" + str(i + 1)
        secstructureseq = secstructureseqlib[secname]
        ASDrandomregion = secstructureseq[index+4:index + 10]
        if "(" in ASDrandomregion or ")" in ASDrandomregion or "{" in ASDrandomregion or "}" in ASDrandomregion or "[" in ASDrandomregion or "]" in ASDrandomregion:
            del Library[ASDname]
            del Library[SDname]
    Library = updatelibindex(Library)
    print('Library after step 5: ',Library)
    return Library

# --------------------------Step 6-7-----------------------------------


def narrow_crossbinding(rRNA):
    # Narrow down the library more by eliminating pairs with ASD that has < 1 kcal/mol binding energy with wild type SD
    Library = ASD_2rystructure_narrow(rRNA)
    WtSD = revcomp(rRNA[1534:1540])
    for n in range(0,int(len(Library)/2)):
        ASD = 'ASD' + str(n+1)
        SD = 'SD' + str(n+1)
        if float(RNAduplexval(Library[ASD],WtSD)) < -1:
            del Library[ASD]
            del Library[SD]
    Library = updatelibindex(Library)
    return Library


def orthoribalgorithm():
    # ---------------Calling function-------------------------------------
    with open(r'C:\Users\siddu\Desktop\Python Code\ecoligenome.txt', 'r') as myfile:
        data = myfile.read().replace('\n', '')
    rRNA = data[4166659:4168201]
    rRNA = convertTtoU(rRNA)
    Libraryafterstep7 = narrow_crossbinding(rRNA)
    return Libraryafterstep7


print('Library after step 7: ', orthoribalgorithm())\



