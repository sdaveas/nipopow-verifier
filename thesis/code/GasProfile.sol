// Gas used by transaction: 183443
0       pragma solidity ^0.6.6;
84      contract Contract {
0
0           uint s;
0           address holder;
0
0           constructor (address a) public {
0               holder = a;
0           }
0
89          function foo (uint c) public  {
598             for (uint i=0; i<c; i++ ) {
155069              s = i;
0               }
226             if (s > 1) {
5233                s += 1;
0               }
0           }
0       }




















