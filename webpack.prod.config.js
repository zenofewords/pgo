var config = require('./webpack.config.js')
var MinifyPlugin = require('babel-minify-webpack-plugin')
var WebpackBundleTracker = require('webpack-bundle-tracker')

config.mode = 'production'
config.output.publicPath = ''
config.plugins = config.plugins.concat([
  new MinifyPlugin(),
  new WebpackBundleTracker({filename: './webpack-stats-prod.json'}),
])

module.exports = config
