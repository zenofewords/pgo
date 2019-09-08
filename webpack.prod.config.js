var config = require('./webpack.config.js')
var MiniCssExtractPlugin = require('mini-css-extract-plugin')
var MinifyPlugin = require('babel-minify-webpack-plugin')
var WebpackBundleTracker = require('webpack-bundle-tracker')

config.output.publicPath = ''
config.plugins = [
  new MinifyPlugin(),
  new MiniCssExtractPlugin({filename: '[name]_[hash].css'}),
  new WebpackBundleTracker({filename: './webpack-stats-prod.json'}),
]
config.mode = 'production'

module.exports = config
