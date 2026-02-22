system "d .simulateTest";

testAutoRegSimulateWithNoCst:{
    n:100;
    params:0.20793670441358317 0.15625334330632218 0.08328570101676175 0.10762268507210443 0.12228963258158161 0.07896963026086247;
    cst:0;
    lastSigns:-1 1 1 -1 -1 -1f;

    actual:.simulate.autoRegSimulate[n;params;cst;lastSigns;1];
    expected:-1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 1 1 -1 -1 1 1 -1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 -1 1 1 1 -1 1 -1 1 1 1 1 1 1 -1 -1 -1 -1 -1 -1 -1 -1 1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 1 1 -1 1 -1 1 1 -1 1 1 1 1 1 -1 1 -1h;
    .qunit.assertEquals[actual;expected;"Simulate AR model with constant parameter equal to zero"];
 };

testAutoRegSimulateWithCst:{
    n:100;
    params:0.20793670441358317 0.15625334330632218 0.08328570101676175 0.10762268507210443 0.12228963258158161 0.07896963026086247;
    cst:0.2;
    lastSigns:-1 1 1 -1 -1 -1f;

    actual:.simulate.autoRegSimulate[n;params;cst;lastSigns;1];
    expected:-1 -1 -1 -1 -1 -1 -1 -1 -1 -1 1 -1 -1 -1 1 1 -1 -1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1h;
    .qunit.assertEquals[actual;expected;"Simulate AR model with positive constant parameter"];
 };

testShouldThrowIfLastSignsTooShort:{
    n:100;
    params:0.5 0.3 0.2;
    cst:0;
    lastSigns:1 -1f; / AR model has 3 parameters, but only the last 2 signs are provided

    .qunit.assertThrows[
        .simulate.autoRegSimulate[n;params;cst;;1];
        lastSigns;
        "Size of 'lastSigns' must be >= size of 'params'";
        "Throw if there are not enough last signs provided compared to the number of parameters in the autoregressive model"];
 };
