# KSPPartClean
Very Simple script for removing parts from crafts in save files

## Usage

Simply run the script like so:

`python ksppartclean.py /Games/Kerbal\ Space\ Program/saves/SetecAstronomy/persistent.sfs PartToRemove OtherPartToRemove`

This will scrub any parts named `PartToRemove` or `OtherPartToRemove` from the
vessels in your save file.

It will then write out a new file with `.cleaned` in the name. You can then
rename your old save file (in case something goes wrong) and name the cleaned
file in it's place.

If you'd like to see a list of all parts used by vessels in your file, simply
run the script without any part names:

`python ksppartclean.py /Games/Kerbal\ Space\ Program/saves/SetecAstronomy/persistent.sfs`

This will yield a list like:
```
MK1Fuselage
Mark1-2Pod
PotatoRoid
R8winglet
RAPIER
RCSBlock
RCSFuelTank
RCSTank1-2
SmallGearBay
StandardCtrlSrf
SurfaceScanner
SurveyScanner
adapterSmallMiniShort
advSasModule
airScoop
asasmodule1-2
decoupler1-2
deltaWing
dockingPort1
dockingPort2
...
parachuteRadial
probeCoreOcto
probeStackSmall
radialDecoupler
radialLiquidEngine1-2
roverWheel1
roverWheel2
sasModule
sensorAccelerometer
sensorGravimeter
sensorThermometer
sepMotor1
solarPanels1
solarPanels2
spotLight1
spotLight2
stackDecoupler
stackDecouplerMini
stackSeparator
stationHub
structuralPanel1
strutCube
sweptWing
trussPiece1x
wingConnector3
```

## Additional Notes/Disclaimer

I wrote this to save one of my own files, so it's pretty quick n' dirty. I've
put it online for others in case they run into a similar issue. There are a lot
of situations where it may not work properly, so use at your own risk.

If you encounter cases where it doesn't work and you wish it would, feel free
to file a GitHub issue. I can't promise I'll get to it, but I'd love to help
if I can!
