__author__ = 'claytonmiller'

from pylab import *
from scipy.optimize import leastsq
import csv
import matplotlib.pyplot as plt
from VRFfunctions import *
from VRF_IDFObjectsTemplates import *
import pandas as pd

#LeastSq R^2 Calc
def calcerror(infodict,xdata):
    ss_err=(infodict['fvec']**2).sum()
    ss_tot=((xdata-xdata.mean())**2).sum()
    rsquared=1-(ss_err/ss_tot)
    return (rsquared)

def FTCurves(df,RatEnergy):
    """
    Create EIRFT and CAPFT
    :param TotalData:
    :param RatEnergy:
    :return:
    """
    #Start by aggregating the IWB, ODB, and CapRatio
    """
    IWB,ODB,CapRatio,PowerRatio=[],[],[],[]
    for measurement in TotalData:
        if measurement[0]==100.0:
            IWB.append(measurement[2])
            ODB.append(measurement[3])
            CapRatio.append(measurement[4]/measurement[1])
            PowerRatio.append(measurement[5]/RatEnergy)
    """
    temp=df[df["CombPer"]==100]
    IWB=temp.iloc[:,2]
    ODB=temp.iloc[:,3]
    CapRatio=temp.iloc[:,4]/temp.iloc[:,1]
    PowerRatio=temp.iloc[:,5]/RatEnergy
    npIWB=np.array(IWB)
    IWBmax,IWBmin = max(npIWB),min(npIWB)
    npODB=np.array(ODB)
    ODBmax,ODBmin = max(npODB),min(npODB)
    npCapRatio=np.array(CapRatio)
    npPowerRatio=np.array(PowerRatio)
    #    print npPowerRatio
    #    print npCapRatio

    p0=[0,0,0,0,0,0] # initial guesses

    #Least Square Optimization to find parameters
    CAPFT,cov,infodict,mesg,ier = leastsq(residualsTwoDimBiquadratic,p0,args=(npCapRatio,npIWB,npODB),full_output=1)
    CAPFTerr = calcerror(infodict,npCapRatio)
    #print CAPFT
    #print CAPFTerr
    EIRFT,cov,infodict,mesg,ier = leastsq(residualsTwoDimBiquadratic,p0,args=(npPowerRatio,npIWB,npODB),full_output=1)
    #print EIRFT
    EIRFTerr = calcerror(infodict,npPowerRatio)
    #print EIRFTerr

    #Can Plot to Compare Fit
    #    EIRPredict = FT(npIWB,npODB,EIRFT)
    #    plotcurve(npIWB,npODB,npPowerRatio,EIRPredict)

    return CAPFT,EIRFT,CAPFTerr,EIRFTerr,IWBmax,IWBmin,ODBmax,ODBmin

#Creates EIRModFunctions - Modifies EIRRatio as a function of CombRatio
def EIRModifier(df,RatedIWB,RatedODB,RatEnergy):
    """
    CombRatioHi,CapRatioHi,PowerRatioHi=[],[],[]
    CombRatioLo,CapRatioLo,PowerRatioLo=[],[],[]
    for measurement in TotalData:
        print (measurement)
        if measurement[2] == RatedIWB and measurement[3] == RatedODB:
            if measurement[0] > 100.0:
                CapRatioHi.append(measurement[4]/measurement[1])
                PowerRatioHi.append(measurement[5]/RatEnergy)
                CombRatioHi.append(measurement[0])
            elif measurement[0]<= 100.0:
                CapRatioLo.append(measurement[4]/measurement[1])
                PowerRatioLo.append(measurement[5]/RatEnergy)
                CombRatioLo.append(measurement[0])
    """
    Hi = df[df["CombPer"] > 100]
    Lo = df[df["CombPer"] <= 100]

    CapRatioHi=Hi.iloc[:,4]/Hi.iloc[:,1]
    PowerRatioHi = Hi.iloc[:,5] / RatEnergy
    CombRatioHi=Hi.iloc[:,0]
    CapRatioLo = Lo.iloc[:, 4] / Lo.iloc[:, 1]
    PowerRatioLo = Lo.iloc[:, 5] / RatEnergy
    CombRatioLo = Lo.iloc[:, 0]

    npCombRatioHi = np.array(CombRatioHi)
    npPowerRatioHi = np.array(PowerRatioHi)
    npCombRatioLo = np.array(CombRatioLo)
    npPowerRatioLo = np.array(PowerRatioLo)

    #Calc EIRHiModFunction
    p0=[0,0,0] # initial guesses
    #Least Square Optimization to find parameters
    EIRModFTHi,cov,infodict,mesg,ier = leastsq(residualsOneDimQuadratic,p0,
                                             args=(npPowerRatioHi,npCombRatioHi),full_output=1)
    EIRModFTHierr = calcerror(infodict,npPowerRatioHi)
    #print EIRModFT
    #print EIRModFTerr

     #Calc EIRHiModFunction
    p0=[0,0,0,0] # initial guesses
    #Least Square Optimization to find parameters
    EIRModFTLo,cov,infodict,mesg,ier = leastsq(residualsOneDimCubic,p0,
                                             args=(npPowerRatioLo,npCombRatioLo),full_output=1)
    EIRModFTLoerr = calcerror(infodict,npPowerRatioLo)
    #print EIRModFT
    #print EIRModFTerr

    return EIRModFTHi,EIRModFTHierr,EIRModFTLo,EIRModFTLoerr

#Creates Cooling Combination Ratio Correction Factor - Modifies Capacity as a function of CombRatio
#Only applies to Comb Ratios above 100%
def CCRCF(df,RatedIWB,RatedODB):
    #CapRatio,CombRatio=[],[]
    CombDivisor = float(100)
    """
    for measurement in TotalData:
        if measurement[2] == RatedIWB and measurement[3] == RatedODB and measurement[0] > 100:
            CombRatio.append(measurement[0]/CombDivisor)
            CapRatio.append(measurement[4]/measurement[1])
    """
    temp=df[(df["IWB"]==RatedIWB)&(df["ODB"]==RatedODB)&(df["CombPer"]>100)]
    CombRatio=temp.iloc[:,0]/CombDivisor
    CapRatio = temp.iloc[:,4]/temp.iloc[:,1]
    npCapRatio=np.array(CapRatio)
    npCombRatio=np.array(CombRatio)

    #Calc Linear Cooling Combination Ratio Correction Factor
    p0=[0,0] # initial guesses
    #Least Square Optimization to find parameters
    CCRCFactor,cov,infodict,mesg,ier = leastsq(residualsOneDimLinear,p0,args=(npCapRatio,npCombRatio),full_output=1)
    CCRCFactorErr = calcerror(infodict,npCapRatio)

    return CCRCFactor,CCRCFactorErr

def plotcurve(X,Y,Z,Z2):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(X, Y, Z)
    ax.scatter(X,Y,Z2)
    plt.show()

#Load TotalData Array from Text file output of CellParser.py
#These code may be able to replace by pandas
"""
TotalData = []
csvreader = csv.reader(open("RXYQ18Cool.xls",newline='',encoding='ascii'),quoting=csv.QUOTE_NONNUMERIC)


for row in csvreader:
    print (row)
    TotalData.append(row)
for row in TotalData[1:]:
    for item in row[1:]:
        item=float(item)
    for item in row[:0]:
        item=int(item)
"""
TotalData=pd.read_csv("test.csv")

#Find Cooling Cooling Capacity Ratio Modifier Function (CAPFT)
# and Energy Input Ratio Modifier Function (EIRFT)
#This script is designed to simplify the process described in:
#https://securedb.fsec.ucf.edu/pub/pub_show_detail?v_pub_id=4588 by neglecting to created a High AND Low
#Performance curves.
RatedCoolingEnergy = 16.2
CAPFT,EIRFT,CAPFTerr,EIRFTerr,IWBmax,IWBmin,ODBmax,ODBmin = FTCurves(TotalData,RatedCoolingEnergy)

#Convert Numpy arrays back to lists for output
CAPFTlist = (CAPFT.tolist())
EIRFTlist = (EIRFT.tolist())

#Find Cooling Energy Input Ratio Modifier Functions -
#Hi = CombRatio >100, Lo = CombRatio <= 100
RatedIWB = 19
RatedODB = 35

EIRModFTHi,EIRFTHierr,EIRModFTLo,EIRModFTLoerr = EIRModifier(TotalData,RatedIWB,RatedODB,RatedCoolingEnergy)

#print EIRModFT,EIRFTerr,EIRModFTLo,EIRModFTLoerr

EIRModFTHi = (EIRModFTHi.tolist())
EIRModFTLo = (EIRModFTLo.tolist())

#Find Cooling Combination Ratio Correction Factor
RatedCap = 49

CCRCFactor, CCRCFactorErr = CCRCF(TotalData,RatedIWB,RatedODB)

#Print Errors
print (CAPFTerr, EIRFTerr, EIRModFTLoerr, EIRFTHierr, CCRCFactorErr)

CurveObjectFile = open("CoolingCurveObjects.txt","w")
CurveObjectFile.write(CoolingCapModifierFunction(CAPFTlist))
CurveObjectFile.write(EnergyInputRatioModifierFunction(EIRFTlist))
CurveObjectFile.write(EnergyInputRatioModifierPartLoadLow(EIRModFTLo))
CurveObjectFile.write(EnergyInputRatioModifierPartLoadHigh(EIRModFTHi))
CurveObjectFile.write(CoolingCombinationRatioCorrectionFactor(CCRCFactor))
CurveObjectFile.write(CPLFFPLR())
CurveObjectFile.write(CoolingLengthCorrectionFactor())









