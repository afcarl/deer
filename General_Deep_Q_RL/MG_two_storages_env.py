import numpy as np
import MG_data
np.set_printoptions(threshold=np.nan)

from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import matplotlib.pyplot as plt
from base_classes import Environment


class MyEnv(Environment):
    def __init__(self, rng):
        """ Initialize environment

        Arguments:
            rng - the numpy random number generator
        """
        # Defining the type of environment
        self._nActions = 3                     # The environment allows two different actions to be taken at each time step
        self._lastPonctualObservation = [0. ,np.array([0.,0.]),0., np.array([0.,0.])] # At each time step, the observation is made up of two elements, each scalar
        self._batchDimensions = [(1,), (12,2), (1,),(1,2)]   # We consider a belief state made up of an history of
                                               # - the last six for the first element obtained
                                               # - the last one for the second element
        self._initState()

        self.rng = rng

        # Get consumption profile in [0,1]
        self.consumption_norm=np.load("data/example_determinist_cons_train.npy")[0:365*24]
        # Scale consumption profile in [0,2.7kW]
        self.consumption=self.consumption_norm*1.7

        self.min_consumption=min(self.consumption)
        self.max_consumption=max(self.consumption)
        print "Sample of the consumption profile (kW): " + str(self.consumption[0:24])
        print "Min of the consumption profile (kW): " + str(self.min_consumption)
        print "Max of the consumption profile (kW): " + str(self.max_consumption)
        print "Average consumption per day (kWh): " + str(np.sum(self.consumption)/self.consumption.shape[0]*24)

        # Get production profile in W/Wp in [0,1]
        self.production_train_norm=np.load("data/BelgiumPV_prod_train.npy")[0:1*365*24]
        self.production_valid_norm=np.load("data/BelgiumPV_prod_train.npy")[365*24:2*365*24]
        #self.production_test_norm=np.load("data/BelgiumPV_prod_test.npy")[0:1*365*24]
        # Scale production profile : 12KWp (60m^2) et en kWh
        self.production_train=self.production_train_norm*12000/1000
        self.production_valid=self.production_train_norm*12000/1000
        #self.production_test=self.production_train_norm*12000/1000

        self.min_production=min(self.production_train)
        self.max_production=max(self.production_train)
        print "Sample of the production profile (kW): " + str(self.production_train[0:24])
        print "Min of the production profile (kW): " + str(self.min_production)
        print "Max of the production profile (kW): " + str(self.max_production)
        print "Average production per day (kWh): " + str(np.sum(self.production_train)/self.production_train.shape[0]*24)

        
        self.battery_size=15.
        self.battery_eta=0.9
        
        self.hydrogen_max_power=1.1
        self.hydrogen_eta=.65
        
    def reset(self, testing):
        """
        Returns:
           current observation (list of k elements)
        """
        ### Test 6
        self._lastPonctualObservation=[1., np.array([0.,0.]),0 , np.array([0.,0.])]#,0]#, [0.,0.]]
        self._initState()

        self.counter = 1        
        self.hydrogen_storage=0.
        
        if testing==True:
            self.production_norm=self.production_train_norm
            self.production=self.production_train
        else:
            self.production_norm=self.production_valid_norm
            self.production=self.production_valid
        
    def act(self, action, testing):
        """
        Perform one time step on the environment
        """
        #print "NEW STEP"

        reward = 0#self.ale.act(action)  #FIXME
        terminal=0

        true_demand=self.consumption[self.counter]-self.production_train[self.counter]
        
        if (action==0):
            ## Energy is taken out of the hydrogen reserve
            true_energy_avail_from_hydrogen=-self.hydrogen_max_power*self.hydrogen_eta
            diff_hydrogen=-self.hydrogen_max_power
        if (action==1):
            ## No energy is taken out of/into the hydrogen reserve
            true_energy_avail_from_hydrogen=0
            diff_hydrogen=0
        if (action==2):
            ## Energy is taken into the hydrogen reserve
            true_energy_avail_from_hydrogen=self.hydrogen_max_power/self.hydrogen_eta
            diff_hydrogen=self.hydrogen_max_power
            
        reward=diff_hydrogen*0.1 # 0.1euro/kWh of hydrogen
        self.hydrogen_storage+=diff_hydrogen

        Energy_needed_from_battery=true_demand+true_energy_avail_from_hydrogen
        
        if (Energy_needed_from_battery>0):
        # Lack of energy
            if (self._lastPonctualObservation[0]*self.battery_size>Energy_needed_from_battery):
            # If enough energy in the battery, use it
                self._lastPonctualObservation[0]=self._lastPonctualObservation[0]-Energy_needed_from_battery/self.battery_size
            else:
            # Otherwise: use what is left and then penalty                
                reward=-(Energy_needed_from_battery-self._lastPonctualObservation[0]*self.battery_size)*2 #2euro/kWh
                self._lastPonctualObservation[0]=0
        if (Energy_needed_from_battery<0):
        # Surplus of energy --> load the battery
            self._lastPonctualObservation[0]=min(1.,self._lastPonctualObservation[0]-Energy_needed_from_battery/self.battery_size*self.battery_eta)
                    
        
        ### Test
        # self._lastPonctualObservation[0] : State of the battery (0=empty, 1=full)
        # self._lastPonctualObservation[1] : Normalized consumption at current time step (-> not available at decision time)
        # self._lastPonctualObservation[1][1] : Normalized production at current time step (-> not available at decision time)
        # self._lastPonctualObservation[2][0] : Prevision (accurate) for the current time step and the next 24hours
        # self._lastPonctualObservation[2][1] : Prevision (accurate) for the current time step and the next 48hours
        ###
        self._lastPonctualObservation[1][0]=self.consumption_norm[self.counter]
        self._lastPonctualObservation[1][1]=self.production_norm[self.counter]
        self._lastPonctualObservation[2]=abs(self.counter/24-(171))/(365.-171.) #171 days between 1jan and 21 Jun
        self._lastPonctualObservation[3][0]=sum(self.production_norm[self.counter:self.counter+24])/24.*self.rng.uniform(0.75,1.25)
        self._lastPonctualObservation[3][1]=sum(self.production_norm[self.counter:self.counter+48])/48.*self.rng.uniform(0.75,1.25)

                    
        self.counter+=1
                
        return reward

    def batchDimensions(self):
        return self._batchDimensions

    def nActions(self):
        return self._nActions

    def inTerminalState(self):
        return False

    def observe(self):
        return self._lastPonctualObservation     

    def get_summary_perf(self, test_data_set):
        print "summary perf"
        print "self.hydrogen_storage: "+str(self.hydrogen_storage)
        
        for i in range(1):
            battery_level=[]
            production=[]
            consumption=[]
            for elems in test_data_set.elements[i+0:i+100]:
                battery_level.append(elems[0])
                consumption.append(elems[1])
                production.append(elems[1][1])
            
            actions=test_data_set.actions[i+0:i+100]
            
            
            battery_level=np.array(battery_level)*self.battery_size
            consumption=np.array(consumption)*(self.max_consumption-self.min_consumption)+self.min_consumption
            production=np.array(production)*(self.max_production-self.min_production)+self.min_production

            steps=np.arange(100)
            print steps
            print production
            steps_long=np.arange(1000)/10.
            
            
#            host = host_subplot(111, axes_class=AA.Axes)
#            plt.subplots_adjust(left=0.2, right=0.8)
#            
#            par1 = host.twinx()
#            par2 = host.twinx()
#            par3 = host.twinx()
#            
#            offset = 60
#            new_fixed_axis = par2.get_grid_helper().new_fixed_axis
#            par2.axis["right"] = new_fixed_axis(loc="right",
#                                                axes=par2,
#                                                offset=(offset, 0))    
#            par2.axis["right"].toggle(all=True)
#            
#            offset = -60
#            new_fixed_axis = par3.get_grid_helper().new_fixed_axis
#            par3.axis["right"] = new_fixed_axis(loc="left",
#                                                axes=par3,
#                                                offset=(offset, 0))    
#            par3.axis["right"].toggle(all=True)
#            
#            
#            host.set_xlim(-0.9, 99)
#            host.set_ylim(0, 15.9)
#            
#            host.set_xlabel("Time")
#            host.set_ylabel("Battery level")
#            par1.set_ylabel("Consumption")
#            par2.set_ylabel("Production")
#            par3.set_ylabel("H Actions")
#            
#            p1, = host.plot(steps, battery_level, marker='o', lw=1, c = 'b', alpha=0.8, ls='-', label = 'Battery level')
#            p2, = par1.plot(steps_long-0.9, np.repeat(consumption,10), lw=3, c = 'r', alpha=0.5, ls='-', label = 'Consumption')
#            p3, = par2.plot(steps_long-0.9, np.repeat(production,10), lw=3, c = 'g', alpha=0.5, ls='-', label = 'Production')
#            p4, = par3.plot(steps_long, np.repeat(actions,10), lw=3, c = 'c', alpha=0.5, ls='-', label = 'H Actions')
#            
#            par1.set_ylim(0, 10.09)
#            par2.set_ylim(0, 10.09)
#            par3.set_ylim(-0.09, 2.09)
#            
#            #host.legend(loc=2)#loc=9)
#            
#            host.axis["left"].label.set_color(p1.get_color())
#            par1.axis["right"].label.set_color(p2.get_color())
#            par2.axis["right"].label.set_color(p3.get_color())
#            par3.axis["right"].label.set_color(p4.get_color())
#            
#            plt.savefig("plot.png")
#            
#            plt.draw()
#            plt.show()
#            plt.close('all')



def main():
    rng = np.random.RandomState(123456)
    myenv=Env(rng)

    print "market price"

    #aa, minaa,maxaa=get_market_price()
    #print aa[0:100], minaa,maxaa    

    print "consumption"
    aa, minaa,maxaa=MG_data.get_consumption(100)
    print aa[0:100], minaa,maxaa
    
    print "production"
    aa, minaa,maxaa=MG_data.get_production(0,100)
    aa, minaa,maxaa=MG_data.get_production(365*24,100)
    print aa[0:100], minaa,maxaa
    
    
    print myenv.act(1, False)
    print myenv.act(1, False)
    print myenv.act(0, False)
    print myenv.act(0, False)
    
if __name__ == "__main__":
    main()
