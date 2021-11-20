const { ethers } = require("hardhat");

async function main() {
  const Malthusia = await ethers.getContractFactory("Malthusia");

  const malthusia = await Malthusia.deploy();
  console.log("Contract deployed to address:", malthusia.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
