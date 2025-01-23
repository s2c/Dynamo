import numpy as np
import pandas as pd

class GammaFunctions:
  def numericGamma(self, number=1):
    '''
    Returns a fixed numeric price reduction factor
    input:
      number: A single number
    '''
    return number

  def truncated_exp_OP(self, threshold = 1, how_many=1):
    '''
    Prebaked Gamma function available to use. Truncates exponential function outputs to 
    inputs:
      threshold: Threshold value for gamma. Value cannot be higher than this
      howMany: Number of values needed
    '''
    np.random.seed(0)
    curr = np.random.exponential(size=how_many, scale = 1)
    while (curr[0]>threshold):
      curr = np.random.exponential(size=how_many, scale = 1)      
    return curr[0]
  
