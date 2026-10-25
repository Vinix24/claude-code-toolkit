const {data, fixtures, createChecker, runCase} = require('./helpers.cjs');
const checker = createChecker(data);
process.stdout.write(JSON.stringify(fixtures.cases.map(item => runCase(checker, item))));
