
import "./symbolicRepresentation/ERC20s_CVL.spec";
import "./symbolicRepresentation/Math_CVL.spec";


/***

Base definitions used in all of Hub spec files

Here we have only safe assumptions, safe summarization that are either proved in math.spec or a nondet summary

***/

methods {
    
    function _.mulDivDown(uint256 a, uint256 b, uint256 c) internal => 
        mulDivDownCVL(a,b,c) expect uint256;
    
    function _.mulDivUp(uint256 a, uint256 b, uint256 c) internal => 
        mulDivUpCVL(a,b,c) expect uint256;

    function _.rayMulDown(uint256 a, uint256 b) internal  => 
        mulDivRayDownCVL(a,b) expect uint256;

    function _.rayMulUp(uint256 a, uint256 b) internal  => 
        mulDivRayUpCVL(a,b) expect uint256;
    
    function _.rayDivDown(uint256 a, uint256 b) internal  => 
        mulDivDownCVL(a,RAY,b) expect uint256;
    
    function _.fromRayUp(uint256 a) internal => 
        divRayUpCVL(a) expect uint256;

    function _.toRay(uint256 a) internal => 
        mulRayCVL(a) expect uint256;

    function PercentageMath.percentMulDown(uint256 percentage, uint256 value) internal returns (uint256) =>  
        mulDivDownCVL(value,percentage,PERCENTAGE_FACTOR);
    
    function _.setInterestRateData(uint256 assetId, bytes data) external => NONDET; 

    function _._checkCanCall(address caller, bytes calldata data) internal => NONDET; 
    
    function _.calculateInterestRate(uint256 assetId, uint256 liquidity, uint256 drawn, uint256 deficit, uint256 swept) external  => NONDET;
}


persistent ghost uint256 RAY {
    axiom RAY == 10^27;
    }

persistent ghost uint256 PERCENTAGE_FACTOR {
    axiom PERCENTAGE_FACTOR == 10000;
    }
 