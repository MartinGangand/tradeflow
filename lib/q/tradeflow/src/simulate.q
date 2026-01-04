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
    if[count[params] > count lastSigns;'"Size of lastSigns must be >= size of parameters"];
    system "S ",string seed;
    reversedParams:reverse params;
    lastSigns:`short$neg[count params]#lastSigns;
    unif:size?1f;
    pred:();
    do[size;
        nextSign:simulateNext[reversedParams;cst;lastSigns;unif count pred];
        pred,:nextSign;
        lastSigns:1_lastSigns,nextSign];
    pred
 }

simulateNext:{[reversedParams;cst;lastSigns;unif]
    ev:cst+sum reversedParams*lastSigns;
    buyProba:.5*1+ev;
    (-1 1h)unif<buyProba
  }
