import numpy as np
import pandas as pd


class Product():
  '''
  Class that captures product attributes
  '''

  def __init__(self, 
               productName,
               peakHour,
               basePrice,
               forecastDF,
               shelfLife,
               elasticFunc,
               elasticFuncArgs,
               curAge=0,
               curPrice=None,
               ):
    '''
      productName: String name of the product
      basePrice: The base price of a given product
      peakHour: Integer between and inclusive of 0-23 which corresponds to the hour with the most sales for that product. In case of bimodal, we use the first peak hour.
      forecastDF: Forecast of the demand for a given day in the form of a pandasDF. First column is "hour" between 0 and 23 inclusive, 2nd column is "demand" as an integerj gfdsaz
      shelfLife: The number of hours that is the shelf life of this product (max age)
      curAge: The current age of the product expressed as hours passed
    '''
    self.productName = productName
    self.peakHour = peakHour
    self.forecastDF = forecastDF
    self.basePrice = basePrice
    self.shelfLife = shelfLife
    self.elasticFunc = elasticFunc
    self.elasticFuncArgs = elasticFuncArgs
    self.curAge = curAge
    if curPrice is not None:
      self.curPrice = curPrice
    else:
      self.curPrice = basePrice 
  
  def getElasticity(self): 
    '''
    Returns associated elasticity
    '''
    return self.elasticFunc(*self.elasticFuncArgs)
    



