const config = require('./webpack.dev.js')
const { CleanWebpackPlugin } = require('clean-webpack-plugin')

config.mode = 'production'
config.devtool = ''
config.output.publicPath = ''
config.plugins.find(
  obj => obj['options']['filename'] === './webpack-stats.json'
)['options']['filename'] = './webpack-stats-prod.json'
config.plugins = [...config.plugins, new CleanWebpackPlugin()]
module.exports = config
