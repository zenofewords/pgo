var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')
var config = require('./webpack.base.config.js')
var CompressionPlugin = require("compression-webpack-plugin")


config.output.path = require('path').resolve('./assets/bundles')
config.output.publicPath = 'http://localhost:3000/assets/bundles/'

config.plugins = config.plugins.concat([
  new webpack.NoEmitOnErrorsPlugin(),
  new BundleTracker({filename: 'webpack/webpack-stats.json'}),
  new webpack.NoEmitOnErrorsPlugin(),
])

config.module.loaders.push(
  { test: /\.jsx?$/, exclude: /node_modules/, loader: 'babel-loader' }
)

module.exports = config
