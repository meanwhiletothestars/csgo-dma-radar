# CSGO DMA RADAR
Easy csgo radar created with python
# requirements
1. DMA Card with pcileech and vmm
2. Second x64 pc
# install
1. Download release
2. Install python 3
3. Install dependencies(memprocfs,pygame,pygame_gui)
4. Open csgo and connect to the map
5. Change map in map.txt
6. Start with /python main.py

# TROUBLESHOOTING
1. download binaries from https://github.com/ufrisk/pcileech
2. start dma test with
```
sudo ./pcileech -device fpga probe
```
(1-8% loss is normal)

4. if test isn't working there is couple of things u can do
   a) try another windows version(downgrade for 21h2 for example)
   b) try to buy other dma firmware 
