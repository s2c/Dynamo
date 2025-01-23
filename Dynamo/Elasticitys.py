import numpy as np
import pandas as pd


class ElasticityFunctions:

  def numericElasticity(self, number=4):
    '''
    Returns a fixed numeric elasticity
    input:
      number: A single number
    '''
    return number

  def linearPieceWise(self, curDiscount, noPieces):
    '''
      curDiscount: The discount on the product relative to the base price
      noPieces: Number of distinct discount "zones" on the pricing curve
    '''
    
    pass