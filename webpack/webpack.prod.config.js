var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')
var config = require('./webpack.base.config.js')
var MinifyPlugin = require('babel-minify-webpack-plugin')

config.output.filename = '[name]-[hash].js'
config.output.path = require('path').resolve('./assets/prod')

config.plugins = config.plugins.concat([
  new BundleTracker({
    filename: 'webpack/webpack-stats-prod.json',
  }),
  new webpack.DefinePlugin({
    'process.env.NODE_ENV': '"production"',
  }),
  new MinifyPlugin(),
  new webpack.NoEmitOnErrorsPlugin(),
])

config.module.loaders.push(
  { test: /\.jsx?$/, exclude: /node_modules/, loader: 'babel-loader' }
)

module.exports = config
