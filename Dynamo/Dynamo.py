import numpy as np
import pandas as pd

class Dynamo:
    hours = [i for i in range(0,24)] #Time Counter
    curHour = 0 
    def __init__(self, 
               product,
               actualDemandDF,
               gamma,
               gammaArgs,
               inventoryAtBeginningOfDay,
               priceCapLow = 0.5,
               priceCapHigh = 1.5,
               closingHour = 23,
               openingHour = 0,
               startAtPeakHour = True,
               minDeltaDiff = 0,
               deltaAdjustmentFactor = 0.8,
               shelfAdjustmentFactor = 0.8,
               ):
      '''
      product: Product object
      actualDemandDF: A DF that has the actual demand for a day. First column is "hour" between 0 and 23 inclusive, 2nd column is "demand" as an integer
      gamma: Price reducion function, a function that generates a number between 0 to 1
      gammaArgs: Gamma function inputs that are needed to generate a number
      inventoryAtBeginningOfDay: inventory of the product at the beginning of the day as an integer
      PriceCapLow: Price drops are capped to the basePrice if the product*PriceCapLow
      PriceCapHigh:Price increases are capped to the basePrice if the product*PriceCapHigh
      closingHour: The last hour of the day
      openingHour: The first hour of the day
      startAtPeakHour: If True, only change prices post the peak hour
      minDeltaDiff: The minimum absolute change from forecast for price changes to occur
      shelfLifeAdjustmentFactor:Accelerates gamma based on remaining shelf life, otherwise continues with the normal decay.  1 is off
      deltaAdjustmentFactor = The ratio of actual to forecasted demand, below which the gamma is adjusted. 1 is off
      '''
      self.product = product
      self.actualDemand = actualDemandDF
      self.gamma = gamma
      self.gammaArgs = gammaArgs
      self.inventory = inventoryAtBeginningOfDay
      self.closingHour = closingHour
      self.openingHour = openingHour
      self.startAtPeakHour = startAtPeakHour
      self.deltaAdjustmentFactor = deltaAdjustmentFactor 
      self.shelfAdjustmentFactor = shelfAdjustmentFactor 
      self.priceCapLow   = priceCapLow 
      self.priceCapHigh = priceCapHigh
      self.minDeltaDiff = minDeltaDiff
      # COUNTERACTUALS
      self.demandLambda = self.product.forecastDF.merge(self.actualDemand, how = 'left', on ='hour') # Merge forecasted and actual demand for the day
      ###############
      ##############
      self.demandLambda['actualdemand'] = 0.8*self.demandLambda['lambda']

      self.demandLambda['cum_actualdemand']= self.demandLambda['actualdemand'].cumsum().astype(int) # total counterfactual demand up to a given hour
      self.demandLambda['cum_forecast']= self.demandLambda['lambda'].cumsum().astype(int) # Total forecasted demand up to a given hour
      self.demandLambda['delta']= self.demandLambda['cum_actualdemand'] - self.demandLambda['cum_forecast'] # Counterfactual difference between forecast and actual
      self.demandLambda['price'] = self.product.basePrice 
      # The New price on an hourly basis, initially set to base price
      self.demandLambda['newPrice'] = self.product.basePrice
      self.demandLambda = self.demandLambda.set_index('hour')

      # To be updated hourly, setting the base state
      self.demandLambda['newactualdemand'] = self.demandLambda['actualdemand'] # Updated inside runSimulation
      self.demandLambda['cum_newactualdemand']= self.demandLambda['newactualdemand'].cumsum().astype(int) # updated inside _updateDemandLambda
      self.demandLambda['currDelta'] = self.demandLambda['cum_newactualdemand'] - self.demandLambda['cum_forecast'] # updated inside _updateDemandLambda
      self.demandLambda['cum_newactualdemand']= self.demandLambda['newactualdemand'].cumsum().astype(int) # updated inside _updateDemandLambda

  
    def runSimulation(self):
      #display(self.demandLambda)

      curHour = 0
      while curHour <= self.closingHour: #
        #print(curHour)
        if (
              (curHour < self.openingHour)   # The store hasn't opened yet, so continue passing time OR IF
            | ((self.startAtPeakHour==True) & (curHour <= self.product.peakHour)) # We want to wait till peak hour has been reached before changing prices
            ):
          curHour += 1
          # print('here')
          continue
        #print('here')
        curDelta = self.demandLambda['currDelta'][curHour] 
        #print(curDelta)

        if abs(curDelta) >= abs(self.minDeltaDiff): # Check if we are at least minDeltaDiff units away from the expected forecast

          if curDelta < 0: # We are behind forecast
            basePrice = self.demandLambda['price'][curHour]
            currGamma = self.gamma(*self.gammaArgs)  # Product a gamma using the gamma function and the gamma args. Gamma is the (exponential) price reduction factor. Between 0 and 1

            if self.deltaAdjustmentFactor != 1: # Delta adjustment option for gamma
              currActualToForecastRatio = self.demandLambda['cum_newactualdemand'][curHour]/self.demandLambda['cum_forecast'][curHour] # How close to forecast are we in % terms?
              if currActualToForecastRatio < self.deltaAdjustmentFactor: # Are we TOO below the prediction?
                currGamma = currGamma/currActualToForecastRatio 
  #######################################################################
            if self.shelfAdjustmentFactor != 1: # Shelf Life adjustment for how close we are to the end of the shelf life of the product
              #currToActualTimePassed= (curHour/(self.product.shelfLife-(24-self.closingHour))) # Proportion of time that has passed for the product
              currToActualTimePassed= (curHour/(self.product.shelfLife)) # Proportion of time that has passed for the product
              if currToActualTimePassed > self.shelfAdjustmentFactor: # Acceleration
                currGamma = currGamma / self.shelfAdjustmentFactor  
  #######################################################################   

            newPrice = basePrice*(1-(curHour/self.product.shelfLife))**currGamma # Calculate newPrice with any associated gamma accelerations
            # To Do: Make this a function instead of just giving the user a way to set the parameter
          # Price cannot exceed the preset Price cap limits
            if newPrice < (basePrice*self.priceCapLow):
              newPrice = basePrice*self.priceCapLow
            
            if newPrice > (basePrice*self.priceCapHigh):
              newPrice = basePrice*self.priceCapHigh
            
            self.product.curPrice = newPrice  
            self.demandLambda['newPrice'][curHour] = newPrice # Price at the beginning of the price
  #######################################################################

            # Get New demands based on updated price
            elasticity = self.product.getElasticity()
            newDemand = (self.demandLambda['actualdemand'][curHour]) *(newPrice/self.product.basePrice)**(-elasticity)
            
            # self.demandLambda['excessDemand'][curHour] = newDemand # Uncapped
            print('iteration')
            print(curHour)
            print(self.inventory)
            print(newDemand)

            if  (self.inventory - newDemand) < 0: # Cap the newactualdemand based on inventory
              newDemand = self.inventory
              self.inventory = 0
            else:
              self.inventory -= newDemand

            self.demandLambda['newactualdemand'][curHour] = newDemand

          

        self._updateDemandLambda()
        curHour += 1
        self.product.curAge += 1 
          # Add in the running waste and revenue metrics
#######################################################################
    
    def _updateDemandLambda(self):
      '''
      Function that is called every hour to update the demandLambda DataFrame
      '''
      self.demandLambda['cum_newactualdemand']= self.demandLambda['newactualdemand'].cumsum().astype(int)

      self.demandLambda['currDelta'] = self.demandLambda['cum_newactualdemand'] - self.demandLambda['cum_forecast']
    

    def getResults(self):
      '''
       Gets the resulting waste, revenue and quantity sold metrics
      '''
      wasteCounterfactual = self.demandLambda['cum_forecast'][self.closingHour]  - self.demandLambda['cum_actualdemand'][self.closingHour] 
      waste =  self.demandLambda['cum_forecast'][self.closingHour] - self.demandLambda['cum_newactualdemand'][self.closingHour] 
      revenueCounterfactual = np.sum(self.demandLambda['actualdemand']*self.demandLambda['price'])
      revenue = np.sum(self.demandLambda['newactualdemand']*self.demandLambda['newPrice'])
      
      # return wasteCounterFactual, waste, revenueCounterFactual,
      return self.demandLambda, wasteCounterfactual, waste, revenueCounterfactual, revenue

