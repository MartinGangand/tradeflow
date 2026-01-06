system "d .simulateTest";

testArSimulateWithNoCst:{
    n:100;
    params:0.20793670441358317 0.15625334330632218 0.08328570101676175 0.10762268507210443 0.12228963258158161 0.07896963026086247;
    cst:0;
    lastSigns:-1 1 1 -1 -1 -1f;

    actual:.simulate.autoRegSimulate[n;params;cst;lastSigns;1];
    expected:-1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 1 1 -1 -1 1 1 -1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 -1 1 1 1 -1 1 -1 1 1 1 1 1 1 -1 -1 -1 -1 -1 -1 -1 -1 1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 1 1 -1 1 -1 1 1 -1 1 1 1 1 1 -1 1 -1h;
    .qunit.assertEquals[actual; expected; "Simulate AR model with constant parameter equal to zero"];
 };

testArSimulateWithCst:{
    n:100;
    params:0.20793670441358317 0.15625334330632218 0.08328570101676175 0.10762268507210443 0.12228963258158161 0.07896963026086247;
    cst:0.2;
    lastSigns:-1 1 1 -1 -1 -1f;

    actual:.simulate.autoRegSimulate[n;params;cst;lastSigns;1];
    expected:-1 -1 -1 -1 -1 -1 -1 -1 -1 -1 1 -1 -1 -1 1 1 -1 -1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1h;
    .qunit.assertEquals[actual; expected; "Simulate AR model with positive constant parameter"];
 };

testShouldThrowIfLastSignsTooShort:{
    n:100;
    params:0.5 0.3 0.2;
    cst:0;
    lastSigns:1 -1f;

    .qunit.assertThrows[
        .simulate.autoRegSimulate[n;params;cst;;1];
        lastSigns;
        "Size of lastSigns must be >= size of parameters";
        "Throw if lastSigns size is less than number of parameters"];
 };
