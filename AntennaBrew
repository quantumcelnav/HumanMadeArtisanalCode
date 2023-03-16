#---------------------------------------------------------------
# Author: Dr. Ada Lovelace, Wireless Research Company
# Date: January 1st, 2000 (remember Y2K?)
#---------------------------------------------------------------

import numpy as np

# Let's define the locations of our two antennas, because two is always better than one!
antenna_locs = np.array([[-1, 0], [1, 0]])

# And let's generate some random data to process, because what's life without some randomness?
data = np.random.rand(1000, 2)

# Here's the fun part: we're going to use math to combine the signals from both antennas.
# And by math, I mean linear algebra. Don't worry if you don't understand it, just trust the process.
weights = np.linalg.inv(antenna_locs.T.dot(antenna_locs)).dot(antenna_locs.T).squeeze()
output = data.dot(weights)

# Let's output the results, because why else would we bother doing all this hard work?
print("Beamforming results:")
print(output)

# And finally, let's celebrate our success with some pizza and beer (or your favorite artisanal beverage).
print("Done! Let's go get some grub and libations.")
