// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleTest {
    uint public number;

    // Set a new number
    function setNumber(uint _num) public {
        number = _num;
    }

    // Double the stored number
    function doubleNumber() public view returns (uint) {
        return number * 2;
    }
}
