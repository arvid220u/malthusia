export function blockToRound(block, init_block) {
  // this should be a piece-wise linear function, I believe. remember to not change the past, but feel free to change the future
  return 2*(block - init_block);
}

// valueToRobotType maps a cost to a robot type
// we specify robot types using costs. this allows us to have flexibility: for example, we might define
// a cost that is lower, but gives a probability over different robot types.
// invalid values lead to no robot...
// remember to not change the past.
export function valueToRobotType(value) {
  if (value === (10 ** 16).toString()) {
    return 0; // WANDERER
  }
  return -1; // NONE
}
