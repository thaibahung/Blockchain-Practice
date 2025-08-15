const { InfuraProvider } = require("ethers");

const provider = new InfuraProvider("mainnet", "67d4fda1bfc248aaba4b1ac954169e08");
const routerAddress = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D";

const exactOutputSelectors = [
  "0x8803dbee", // swapTokensForExactTokens
  "0x4a25d94a", // swapETHForExactTokens
];

async function findExactOutputSwaps(startBlock, endBlock) {
  for (let block = startBlock; block <= endBlock; block++) {
    // Use getBlock with includeTransactions in ethers v6
    const blockData = await provider.getBlock(block, { includeTransactions: true });
    // console.log(`Scanning block ${block} with ${blockData.transactions.length} transactions`);
    for (const tx of blockData.transactions) {
        console.log({
            hash: tx.hash,
            to: tx.to,
            from: tx.from,
            data: tx.data,
            value: tx.value.toString(),
            });
        if (tx.to) {
        console.log(`Checking tx ${tx.hash} in block ${block}`);
        if (tx.to.toLowerCase() === routerAddress.toLowerCase()) {
          console.log(`Found tx to router: ${tx.hash}`);
          if (tx.data && exactOutputSelectors.some(sel => tx.data.startsWith(sel))) {
            console.log(`Exact output swap tx found: ${tx.hash} at block ${block}`);
          }
        }
      }
    }
  }
}

console.log("Starting scan for exact output swaps...");
// Example: scan blocks
findExactOutputSwaps(17300000, 17300100);
