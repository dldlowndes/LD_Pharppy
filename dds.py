import driver
import sys
#import time

#dev = driver.Novatech409B('COM4')

port = sys.argv[1]
ch = int(sys.argv[2])
freq = float(sys.argv[3])
# static. frequency in MHz
dev = driver.Novatech409B(port)
dev.set_freq(ch, freq)
dev.set_gain(ch,1) #V_pp in Volts
#while True:
#    time.sleep(0.001)
#    dev.set_gain(ch, 0)
#    time.sleep(0.001)
#    dev.set_gain(ch,0.5)

# table mode. frequency in MHz
#dev.table_init()
#dev.table_write(0, 137.182, 1023, 56.6, 1023)
#dev.table_write(1, 137.182, 1023, 55.4, 1023)
#dev.table_start()
