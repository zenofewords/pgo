var MiniCssExtractPlugin = require('mini-css-extract-plugin')
var path = require('path')
var WebpackBundleTracker = require('webpack-bundle-tracker')


module.exports = {
  entry: {
    breakpointCalc: './static/javascript/breakpointCalc',
    goodToGo: './static/javascript/goodToGo',
    lists: './static/javascript/lists',
  },
  output: {
    filename: '[name]_[hash].js',
    path: path.resolve(__dirname, 'bundles'),
    publicPath: 'http://localhost:3000/static/bundles/',
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /(node_modules)/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env'],
          }
        },
      },
      {
        test: /\.(sa|sc|c)ss$/,
        use: [
          {
            loader: MiniCssExtractPlugin.loader,
          },
          {
            loader: 'css-loader',
          },
          {
            loader: 'sass-loader',
            options: {
              implementation: require('sass'),
            }
          },
        ]
      },
      {
        test: /\.(png|jpe?g|gif|svg)$/,
        use: [
          {
            loader: 'file-loader',
          },
        ]
      },
    ]
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: '[name]_[hash].css',
    }),
    new WebpackBundleTracker({
      filename: 'static/webpack-stats.json'
    }),
  ],
  mode: 'development',
}
