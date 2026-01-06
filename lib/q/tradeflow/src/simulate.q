\d .simulate

// Simulate an autocorrelated sign sequence using an autoregressive model
// @param size {number} Number of signs to generate
// @param params {float[]} Autoregressive model parameters
// @param cst {number} Constant parameter of the model
// @param lastSigns {vector[number]} Last observed or simulated signs (size must be >= number of parameters)
// @param seed {long} Non-zero long value used to re-initialize the seed
// @return {number[]} Simulated signs (+1 for buy, -1 for sell)
// @example
// .simulate.arsim[10; 0.5345669501134418 0.18274445939791428 0.11719456844674148 0.12819588425574271;0;-1 1 1 1;42]
// /=> 1 1 1 -1 1 -1 -1 -1 -1 -1f
autoRegSimulate:{[size;params;cst;lastSigns;seed]
    if[count[params] > count lastSigns;'"Size of lastSigns must be >= size of parameters"]; / Ensure initial window is large enough
    f:simulateNext[reverse params;cst;;];                                                   / Projection with fixed parameters to simulate next sign
    lastSigns:`short$neg[count params]#lastSigns;                                           / Keep only 'count params' last signs
    last each {[f;p;u](1_p),f[p;u]}[f;;]\[lastSigns;generateUniforms[size;seed]]            / Scan iterator to evolve the rolling state and collect the simulated signs
 }

/ Generate a reproducible sequence of uniform random values with seed restoration
generateUniforms:{[size;seed]
    originalSeed:system "S";          / Save current seed
    system "S ",string seed;          / Set new seed for reproducible simulation
    unifs:size?1f;                    / Generate 'size' uniform random numbers
    system "S ", string originalSeed; / Restore original seed to avoid side effects
    unifs
 }

/ Logic for a single autoregressive step to simulate the next sign
simulateNext:{[reversedParams;cst;lastSigns;unif]
    ev:cst+sum reversedParams*lastSigns; / Expected value of next sign (linear combination of last signs)
    buyProba:.5*1+ev;                    / Map expected value to buy probability in [0;1]
    (-1 1h)unif<buyProba                 / Return +1 (buy) with probability buyProba, -1 (sell) otherwise
 }
