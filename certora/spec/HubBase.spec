
import "./symbolicRepresentation/ERC20s_CVL.spec";
import "./symbolicRepresentation/Math_CVL.spec";
import "./common.spec";


/***

Base definitions used in all of Hub spec files

Here we have only safe assumptions, safe summarization that are either proved in math.spec or a nondet summary

***/

methods {
    
    function _.calculateInterestRate(uint256 assetId, uint256 liquidity, uint256 drawn, uint256 deficit, uint256 swept) external  => NONDET;
}


 