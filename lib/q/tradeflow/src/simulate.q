\d .simulate

// Simulate an autocorrelated sign sequence using an autoregressive model
// @param size {number} Number of signs to generate
// @param params {float[]} Autoregressive model parameters (ordered from the parameter associated with the most recent sign to oldest sign)
// @param cst {number} Constant parameter of the model
// @param lastSigns {vector[number]} Last observed signs (vector size must be >= size of 'params')
// @param seed {long} Non-zero long value used to re-initialize the seed of the random generator for reproducibility
// @return {short[]} Simulated signs (+1 for buy, -1 for sell)
// @example
// .simulate.autoRegSimulate[10;0.5345669501134418 0.18274445939791428 0.11719456844674148 0.12819588425574271;0;-1 1 1 1;42]
// /=> 1 1 1 -1 1 -1 -1 -1 -1 -1h
autoRegSimulate:{[size;params;cst;lastSigns;seed]
    p:count params;                                                              / Number of autoregressive parameters
    if[p>count lastSigns;'"Size of 'lastSigns' must be >= size of 'params'"];    / Ensure initial window is large enough
    f:simulateNext[reverse params;cst;;];                                        / Projection with fixed parameters to simulate next sign
    lastSigns:`short$neg[p]#lastSigns;                                           / Keep only 'count params' last signs
    last each {[f;l;u](1_l),f[l;u]}[f;;]\[lastSigns;generateUniforms[size;seed]] / Scan iterator to evolve the rolling state and collect the simulated signs
 }

/ Single autoregressive step (simulates the next sign given history)
/ reversedParams is the vector of autoregressive model parameters aligned with lastSigns, from oldest to most recent sign
simulateNext:{[reversedParams;cst;lastSigns;unif]
    ev:cst+sum reversedParams*lastSigns; / Next sign expected value (linear combination of past signs)
    buyProba:.5*1+ev;                    / Map expected value to buy probability in [0, 1]
    (-1 1h)unif<buyProba                 / Return +1 (buy) with probability buyProba, -1 (sell) with probability 1 - buyProba
 }

/ Generate a reproducible sequence of uniform random values with seed restoration
generateUniforms:{[size;seed]
    originalSeed:system "S";         / Save current seed
    system "S ",string seed;         / Set new seed for reproducibility
    res:@[{x?1f};size;{x}];          / Generate 'size' uniform random numbers (capture result or error message)
    system "S ",string originalSeed; / Restore original seed to avoid side effects
    $[10h=type res;'res;res]         / If 'res' is an error message, throw it, otherwise return the generated uniforms
 }
