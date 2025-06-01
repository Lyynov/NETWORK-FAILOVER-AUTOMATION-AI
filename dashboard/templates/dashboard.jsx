import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { 
  Activity, 
  Wifi, 
  WifiOff, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Zap, 
  Settings, 
  Database,
  Brain,
  Clock,
  TrendingUp,
  TrendingDown,
  RotateCcw
} from 'lucide-react';

const Dashboard = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [interfaces, setInterfaces] = useState([]);
  const [events, setEvents] = useState([]);
  const [aiStatus, setAiStatus] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [selectedInterface, setSelectedInterface] = useState(null);
  const [metricsData, setMetricsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Simulated API calls (replace with actual API endpoints)
  const fetchSystemStatus = useCallback(async () => {
    try {
      // Simulated data - replace with actual API call
      const mockStatus = {
        system_state: 'normal',
        active_interface: 'ether1',
        overall_health_score: 0.92,
        interface_health: {
          ether1: { is_healthy: true, health_score: 0.95, status: 'excellent' },
          ether3: { is_healthy: true, health_score: 0.88, status: 'good' },
          ether4: { is_healthy: false, health_score: 0.45, status: 'degraded' }
        },
        recent_failovers: 2,
        recent_failures: 0,
        uptime_since_last_failover: 86400
      };
      setSystemStatus(mockStatus);
    } catch (err) {
      setError('Failed to fetch system status');
    }
  }, []);

  const fetchInterfaces = useCallback(async () => {
    try {
      // Simulated data - replace with actual API call
      const mockInterfaces = [
        {
          name: 'ether1',
          is_active: true,
          is_primary: true,
          status: 'up',
          health_score: 0.95,
          latency: 12.5,
          packet_loss: 0.1,
          last_update: new Date().toISOString()
        },
        {
          name: 'ether3',
          is_active: false,
          is_primary: false,
          status: 'up',
          health_score: 0.88,
          latency: 18.2,
          packet_loss: 0.3,
          last_update: new Date().toISOString()
        },
        {
          name: 'ether4',
          is_active: false,
          is_primary: false,
          status: 'degraded',
          health_score: 0.45,
          latency: 85.6,
          packet_loss: 2.1,
          last_update: new Date().toISOString()
        }
      ];
      setInterfaces(mockInterfaces);
    } catch (err) {
      setError('Failed to fetch interfaces');
    }
  }, []);

  const fetchEvents = useCallback(async () => {
    try {
      // Simulated data - replace with actual API call
      const mockEvents = [
        {
          id: 1,
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          event_type: 'failover_success',
          source_interface: 'ether3',
          target_interface: 'ether1',
          reason: 'High latency detected',
          success: true,
          duration_seconds: 8
        },
        {
          id: 2,
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          event_type: 'ai_prediction',
          source_interface: 'ether4',
          reason: 'Predicted failure based on degrading metrics',
          success: true
        }
      ];
      setEvents(mockEvents);
    } catch (err) {
      setError('Failed to fetch events');
    }
  }, []);

  const fetchMetricsData = useCallback(async (interfaceName) => {
    try {
      // Generate simulated time series data
      const now = new Date();
      const data = [];
      for (let i = 23; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60 * 60 * 1000);
        data.push({
          timestamp: time.toISOString(),
          time: time.toLocaleTimeString(),
          latency: Math.random() * 50 + (interfaceName === 'ether4' ? 50 : 10),
          packet_loss: Math.random() * (interfaceName === 'ether4' ? 5 : 1),
          health_score: Math.random() * 0.3 + (interfaceName === 'ether4' ? 0.4 : 0.7),
          bandwidth_rx: Math.random() * 100,
          bandwidth_tx: Math.random() * 80
        });
      }
      setMetricsData(data);
    } catch (err) {
      setError('Failed to fetch metrics data');
    }
  }, []);

  useEffect(() => {
    const fetchAllData = async () => {
      setLoading(true);
      await Promise.all([
        fetchSystemStatus(),
        fetchInterfaces(),
        fetchEvents()
      ]);
      setLoading(false);
    };

    fetchAllData();
    
    // Set up real-time updates
    const interval = setInterval(fetchAllData, 10000); // Update every 10 seconds
    
    return () => clearInterval(interval);
  }, [fetchSystemStatus, fetchInterfaces, fetchEvents]);

  useEffect(() => {
    if (selectedInterface) {
      fetchMetricsData(selectedInterface);
    }
  }, [selectedInterface, fetchMetricsData]);

  const handleManualFailover = async (targetInterface) => {
    try {
      // Simulated API call - replace with actual implementation
      console.log(`Manual failover to ${targetInterface}`);
      
      // Update UI optimistically
      setInterfaces(prev => prev.map(iface => ({
        ...iface,
        is_active: iface.name === targetInterface
      })));
      
      // Refresh data after failover
      setTimeout(() => {
        fetchSystemStatus();
        fetchInterfaces();
        fetchEvents();
      }, 1000);
      
    } catch (err) {
      setError('Failed to execute failover');
    }
  };

  const getStatusColor = (status, health_score) => {
    if (status === 'down') return 'text-red-500';
    if (status === 'degraded' || health_score < 0.6) return 'text-yellow-500';
    if (health_score > 0.9) return 'text-green-500';
    return 'text-blue-500';
  };

  const getStatusIcon = (status, is_active) => {
    if (is_active) return <Zap className="w-5 h-5 text-yellow-500" />;
    if (status === 'down') return <WifiOff className="w-5 h-5 text-red-500" />;
    if (status === 'degraded') return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    return <Wifi className="w-5 h-5 text-green-500" />;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Network Failover Dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Dashboard Error</h2>
          <p className="text-gray-600">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <Activity className="w-8 h-8 text-blue-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">Network Failover AI Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${systemStatus?.system_state === 'normal' ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
                <span className="text-sm font-medium text-gray-600">
                  {systemStatus?.system_state === 'normal' ? 'System Normal' : 'System Alert'}
                </span>
              </div>
              <button className="p-2 text-gray-400 hover:text-gray-600">
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200 bg-white rounded-t-lg mt-4">
          <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
            {[
              { id: 'overview', name: 'Overview', icon: Activity },
              { id: 'interfaces', name: 'Interfaces', icon: Wifi },
              { id: 'metrics', name: 'Metrics', icon: TrendingUp },
              { id: 'ai', name: 'AI Analysis', icon: Brain },
              { id: 'events', name: 'Events', icon: Clock }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
              >
                <tab.icon className="w-4 h-4" />
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <CheckCircle className="w-8 h-8 text-green-500" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">System Health</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {Math.round((systemStatus?.overall_health_score || 0) * 100)}%
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Zap className="w-8 h-8 text-yellow-500" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Active Interface</p>
                    <p className="text-2xl font-bold text-gray-900">{systemStatus?.active_interface}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <RotateCcw className="w-8 h-8 text-blue-500" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Failovers (24h)</p>
                    <p className="text-2xl font-bold text-gray-900">{systemStatus?.recent_failovers || 0}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Clock className="w-8 h-8 text-purple-500" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Uptime</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {Math.round((systemStatus?.uptime_since_last_failover || 0) / 3600)}h
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Interface Status Overview */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Interface Status</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {interfaces.map((iface) => (
                    <div key={iface.name} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(iface.status, iface.is_active)}
                          <span className="font-medium">{iface.name}</span>
                          {iface.is_primary && (
                            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">Primary</span>
                          )}
                          {iface.is_active && (
                            <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">Active</span>
                          )}
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Health Score:</span>
                          <span className={`font-medium ${getStatusColor(iface.status, iface.health_score)}`}>
                            {Math.round(iface.health_score * 100)}%
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Latency:</span>
                          <span>{iface.latency.toFixed(1)}ms</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Packet Loss:</span>
                          <span>{iface.packet_loss.toFixed(1)}%</span>
                        </div>
                      </div>

                      {!iface.is_active && iface.status !== 'down' && (
                        <button
                          onClick={() => handleManualFailover(iface.name)}
                          className="w-full mt-3 px-3 py-2 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
                        >
                          Switch to {iface.name}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Interfaces Tab */}
        {activeTab === 'interfaces' && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Interface Details</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Interface</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Health</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Latency</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Packet Loss</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Update</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {interfaces.map((iface) => (
                    <tr key={iface.name}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {getStatusIcon(iface.status, iface.is_active)}
                          <div className="ml-3">
                            <div className="text-sm font-medium text-gray-900">{iface.name}</div>
                            <div className="text-sm text-gray-500">
                              {iface.is_primary && 'Primary'} {iface.is_active && 'Active'}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          iface.status === 'up' ? 'bg-green-100 text-green-800' :
                          iface.status === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {iface.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div 
                              className={`h-2 rounded-full ${
                                iface.health_score > 0.8 ? 'bg-green-500' :
                                iface.health_score > 0.6 ? 'bg-yellow-500' :
                                'bg-red-500'
                              }`}
                              style={{ width: `${iface.health_score * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-sm text-gray-900">{Math.round(iface.health_score * 100)}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {iface.latency.toFixed(1)}ms
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {iface.packet_loss.toFixed(1)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(iface.last_update).toLocaleTimeString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => setSelectedInterface(iface.name)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                        >
                          View Metrics
                        </button>
                        {!iface.is_active && iface.status !== 'down' && (
                          <button
                            onClick={() => handleManualFailover(iface.name)}
                            className="text-green-600 hover:text-green-900"
                          >
                            Failover
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Metrics Tab */}
        {activeTab === 'metrics' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-medium text-gray-900">Interface Metrics</h3>
                  <select
                    value={selectedInterface || ''}
                    onChange={(e) => setSelectedInterface(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option value="">Select Interface</option>
                    {interfaces.map((iface) => (
                      <option key={iface.name} value={iface.name}>{iface.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              {selectedInterface && metricsData.length > 0 && (
                <div className="p-6 space-y-6">
                  {/* Latency Chart */}
                  <div>
                    <h4 className="text-md font-medium text-gray-900 mb-4">Latency (24h)</h4>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={metricsData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" />
                        <YAxis />
                        <Tooltip />
                        <Line type="monotone" dataKey="latency" stroke="#3B82F6" strokeWidth={2} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Packet Loss Chart */}
                  <div>
                    <h4 className="text-md font-medium text-gray-900 mb-4">Packet Loss (24h)</h4>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={metricsData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" />
                        <YAxis />
                        <Tooltip />
                        <Line type="monotone" dataKey="packet_loss" stroke="#EF4444" strokeWidth={2} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Bandwidth Chart */}
                  <div>
                    <h4 className="text-md font-medium text-gray-900 mb-4">Bandwidth Usage (24h)</h4>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={metricsData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="bandwidth_rx" stroke="#10B981" strokeWidth={2} name="RX (Mbps)" />
                        <Line type="monotone" dataKey="bandwidth_tx" stroke="#F59E0B" strokeWidth={2} name="TX (Mbps)" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* AI Analysis Tab */}
        {activeTab === 'ai' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <Brain className="w-5 h-5 mr-2" />
                  AI Analysis & Predictions
                </h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 mb-2">Anomaly Detection</h4>
                    <p className="text-sm text-blue-700">No anomalies detected in the last 24 hours</p>
                    <div className="mt-3 text-xs text-blue-600">
                      Last scan: {new Date().toLocaleTimeString()}
                    </div>
                  </div>
                  
                  <div className="bg-green-50 rounded-lg p-4">
                    <h4 className="font-medium text-green-900 mb-2">Failure Prediction</h4>
                    <p className="text-sm text-green-700">All interfaces show stable patterns</p>
                    <div className="mt-3 text-xs text-green-600">
                      Confidence: 92%
                    </div>
                  </div>
                  
                  <div className="bg-yellow-50 rounded-lg p-4">
                    <h4 className="font-medium text-yellow-900 mb-2">Performance Trends</h4>
                    <p className="text-sm text-yellow-700">ether4 showing degraded performance</p>
                    <div className="mt-3 text-xs text-yellow-600">
                      Recommendation: Monitor closely
                    </div>
                  </div>
                  
                  <div className="bg-purple-50 rounded-lg p-4">
                    <h4 className="font-medium text-purple-900 mb-2">Model Status</h4>
                    <p className="text-sm text-purple-700">Models trained and operational</p>
                    <div className="mt-3 text-xs text-purple-600">
                      Last retrain: 2 hours ago
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Events Tab */}
        {activeTab === 'events' && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recent Events</h3>
            </div>
            <div className="divide-y divide-gray-200">
              {events.map((event) => (
                <div key={event.id} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${
                        event.success ? 'bg-green-500' : 'bg-red-500'
                      }`}></div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {event.event_type.replace('_', ' ').toUpperCase()}
                        </p>
                        <p className="text-sm text-gray-500">{event.reason}</p>
                        {event.source_interface && event.target_interface && (
                          <p className="text-xs text-gray-400">
                            {event.source_interface} → {event.target_interface}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">
                        {new Date(event.timestamp).toLocaleString()}
                      </p>
                      {event.duration_seconds && (
                        <p className="text-xs text-gray-400">
                          Duration: {event.duration_seconds}s
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {events.length === 0 && (
                <div className="px-6 py-8 text-center">
                  <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">No recent events</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Alert Banner */}
      {systemStatus?.system_state !== 'normal' && (
        <div className="fixed bottom-4 right-4 bg-yellow-500 text-white px-6 py-3 rounded-lg shadow-lg">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">System Alert: {systemStatus?.system_state}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
