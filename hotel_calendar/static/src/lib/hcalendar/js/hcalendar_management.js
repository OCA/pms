/* global _, moment */
'use strict';
/*
 * Hotel Calendar Management JS v0.0.1a - 2017-2018
 * GNU Public License
 * Alexandre Díaz <dev@redneboa.es>
 *
 * Dependencies:
 *     - moment
 *     - underscore
 *     - jquery !shit
 *     - bootbox  !shit
 *     - bootstrap  !shit
 */

function HotelCalendarManagement(/*String*/querySelector, /*Dictionary*/options, /*HTMLObject?*/_base) {
  if (window === this) {
    return new HotelCalendarManagement(querySelector, options, _base);
  }

  this.$base = (_base === 'undefined') ? document : _base;

  if (typeof querySelector === 'string') {
    this.e = this.$base.querySelector(querySelector);
    if (!this.e) {
      return false;
    }
  } else if (typeof querySelector === 'object') {
    this.e = querySelector;
  } else {
    return {
      Version: '0.0.1a',
      Author: "Alexandre Díaz",
      Created: "24/09/2017",
      Updated: "21/04/2018"
    };
  }

  /** Strings **/
  this._strings = {
    'Open': 'Open',
    'Closed': 'Closed',
    'C. Departure': 'C. Departure',
    'C. Arrival': 'C. Arrival',
    'Price': 'Price',
    'Availability': 'Availability',
    'Min. Stay': 'Min. Stay',
    'Max. Stay': 'Max. Stay',
    'Min. Stay Arrival': 'Min. Stay Arrival',
    'Max. Stay Arrival': 'Max. Stay Arrival',
    'Clousure': 'Clousure',
    'Free Rooms': 'Free Rooms',
    'No OTA': 'No OTA',
    'Options': 'Options',
    'Reset': 'Reset',
    'Copy': 'Copy',
    'Paste': 'Paste',
    'Clone': 'Clone',
    'Cancel': 'Cancel'
  };

  /** Options **/
  if (!options) { options = {}; }
  this.options = {
    startDate: moment(options.startDate || new Date()),
    days: options.days || moment(options.startDate || new Date()).daysInMonth(),
    rooms: options.rooms || [],
    endOfWeek: options.endOfWeek || 6,
    endOfWeekOffset: options.endOfWeekOffset || 0,
    currencySymbol: options.currencySymbol || '€',
    dateFormatLong: options.dateFormat || 'YYYY-MM-DD HH:mm:ss',
    dateFormatShort: options.dateFormat || 'YYYY-MM-DD',
    translations: options.translations || []
  };

  // Check correct values
  if (this.options.rooms.length > 0 && !(this.options.rooms[0] instanceof HRoomType)) {
    this.options.rooms = [];
    console.warn("[Hotel Calendar Management][init] Invalid Room definiton!");
  }

  // Merge Transalations
  for (var key in this.options.translations) {
    this._strings[key] = this.options.translations[key];
  }

  /** Internal Values **/
  this.tableCreated = false;
  this._pricelist = {};
  this._restrictions = {};
  this._availability = {};
  this._copy_values = {};
  this._mode = HotelCalendarManagement.MODE.ALL;

  /***/
  if (!this._create()) {
    return false;
  }

  return this;
}

HotelCalendarManagement.prototype = {
  /** PUBLIC MEMBERS **/
  addEventListener: function(/*String*/event, /*Function*/callback) {
    this.e.addEventListener(event, callback);
  },

  hasChangesToSave: function() {
    return this.e.querySelector('.hcal-management-record-changed') !== null;
  },

  //==== CALENDAR
  setStartDate: function(/*String,MomentObject*/date, /*Int?*/days) {
    var curDate = this.options.startDate;
    if (moment.isMoment(date)) {
      this.options.startDate = date;
    } else if (typeof date === 'string'){
      this.options.startDate = moment(date);
    } else {
      console.warn("[Hotel Calendar Management][setStartDate] Invalid date format!");
      return;
    }

    if (typeof days !== 'undefined') {
      this.options.days = days;
    }

    /*this.e.dispatchEvent(new CustomEvent(
            'hcOnChangeDate',
            {'detail': {'prevDate':curDate, 'newDate': $this.options.startDate}}));*/
    this._updateView();
  },

  getOptions: function(/*String?*/key) {
    if (typeof key !== 'undefined') {
      return this.options[key];
    }
    return this.options;
  },

  setMode: function(/*Int*/mode) {
    if (typeof mode === 'undefined') {
      mode = this._mode;
    }
    if (mode === HotelCalendarManagement.MODE.LOW) {
      this.etable.classList.remove('hcal-management-medium');
      this.etable.classList.add('hcal-management-low');
      this.edivrhl.classList.remove('hcal-management-medium');
      this.edivrhl.classList.add('hcal-management-low');
      this._mode = HotelCalendarManagement.MODE.LOW;
    } else if (mode === HotelCalendarManagement.MODE.MEDIUM) {
      this.etable.classList.remove('hcal-management-low');
      this.etable.classList.add('hcal-management-medium');
      this.edivrhl.classList.remove('hcal-management-low');
      this.edivrhl.classList.add('hcal-management-medium');
      this._mode = HotelCalendarManagement.MODE.MEDIUM;
    } else {
      this.etable.classList.remove('hcal-management-low');
      this.etable.classList.remove('hcal-management-medium');
      this.edivrhl.classList.remove('hcal-management-low');
      this.edivrhl.classList.remove('hcal-management-medium');
      this._mode = HotelCalendarManagement.MODE.ALL;
    }
  },


  /** PRIVATE MEMBERS **/
  //==== MAIN FUNCTIONS
  _create: function() {
    this.e.innerHTML = "";
    if (this.tableCreated) {
      console.warn("[Hotel Calendar Management] Already created!");
      return false;
    }

    /** Main Table **/
    this.etable = document.createElement("table");
    this.etable.classList.add('hcal-management-table');
    this.etable.classList.add('noselect');
    this.e.appendChild(this.etable);
    this._updateView();
    this.tableCreated = true;

    return true;
  },

  _generateTableDay: function(/*HTMLObject*/parentCell) {
    var $this = this;
    var table = document.createElement("table");
    table.classList.add('hcal-management-table-day');
    table.classList.add('noselect');
    var row = false;
    var cell = false;
    var telm = false;
    var roomId = $this.$base.querySelector(`#${parentCell.dataset.hcalParentRow}`).dataset.hcalRoomObjId;
    var room = $this.getRoom(roomId);
    var dateCell = HotelCalendarManagement.toMoment(parentCell.dataset.hcalDate);
    var dateShortStr = dateCell.format(HotelCalendarManagement._DATE_FORMAT_SHORT);

    row = table.insertRow();
    row.setAttribute('name', 'price');

    cell = row.insertCell();
    cell.setAttribute('colspan', '4');
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`PRICE_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'price');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', this._t('Price'));
    telm.value = room.price;
    telm.dataset.orgValue = room.price;
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input');
    telm.addEventListener('change', function(ev){ $this.onInputChange(ev, this); }, false);
    cell.appendChild(telm);

    row = table.insertRow();
    row.setAttribute('name', 'avail');
    row.style.display = 'none';

    cell = row.insertCell();
    cell.setAttribute('colspan', '1');
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`QUOTA_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'quota');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', this._t('Availability Quota'));
    telm.value = telm.dataset.orgValue = 0;
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input');
    telm.addEventListener('change', function(ev){ $this.onInputChange(ev, this); }, false);
    cell.appendChild(telm);

    cell = row.insertCell();
    cell.setAttribute('colspan', '1');
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`MAX_AVAIL_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'max_avail');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', this._t('Max. Availability'));
    telm.value = telm.dataset.orgValue = 0;
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input');
    telm.addEventListener('change', function(ev){ $this.onInputChange(ev, this); }, false);
    cell.appendChild(telm);

    cell = row.insertCell();
    cell.setAttribute('colspan', '1');
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`FREE_ROOMS_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'free_rooms');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', this._t('Free Rooms'));
    telm.setAttribute('readonly', 'readonly');
    telm.setAttribute('disabled', 'disabled');
    telm.style.backgroundColor = 'lightgray';
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    cell.appendChild(telm);

    cell = row.insertCell();
    cell.setAttribute('colspan', '1');
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`CHANNEL_AVAIL_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'channel_avail');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', this._t('Channel Availability'));
    telm.setAttribute('readonly', 'readonly');
    telm.setAttribute('disabled', 'disabled');
    telm.value = telm.dataset.orgValue = room.channel_avail;
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input');
    cell.appendChild(telm);

    row = table.insertRow();
    row.setAttribute('name', 'rest_a');

    cell = row.insertCell();
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`MIN_STAY_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'min_stay');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', this._t('Min. Stay'));
    telm.dataset.orgValue = telm.value = 0;
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input');
    telm.classList.add('hcal-border-radius-left');
    telm.addEventListener('change', function(ev){ $this.onInputChange(ev, this); }, false);
    cell.appendChild(telm);

    cell = row.insertCell();
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`MAX_STAY_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'max_stay');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', this._t('Max. Stay'));
    telm.dataset.orgValue = telm.value = 0;
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input');
    telm.classList.add('hcal-border-radius-right');
    telm.addEventListener('change', function(ev){ $this.onInputChange(ev, this); }, false);
    cell.appendChild(telm);

    cell = row.insertCell();
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`MIN_STAY_ARRIVAL_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'min_stay_arrival');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', this._t('Min. Stay Arrival'));
    telm.dataset.orgValue = telm.value = 0;
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input');
    telm.classList.add('hcal-border-radius-left');
    telm.addEventListener('change', function(ev){ $this.onInputChange(ev, this); }, false);
    cell.appendChild(telm);

    cell = row.insertCell();
    telm = document.createElement("input");
    telm.setAttribute('id', this._sanitizeId(`MAX_STAY_ARRIVAL_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'max_stay_arrival');
    telm.setAttribute('type', 'edit');
    telm.setAttribute('title', this._t('Max. Stay Arrival'));
    telm.dataset.orgValue = telm.value = 0;
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input');
    telm.classList.add('hcal-border-radius-right');
    telm.addEventListener('change', function(ev){ $this.onInputChange(ev, this); }, false);
    cell.appendChild(telm);

    row = table.insertRow();
    row.setAttribute('name', 'rest_b');
    cell = row.insertCell();
    cell.setAttribute('colspan', '3');
    telm = document.createElement("select");
    telm.classList.add('hcal-management-input');
    telm.addEventListener('change', function(ev){ $this.onInputChange(ev, this); }, false);
    telm.setAttribute('id', this._sanitizeId(`CLOUSURE_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'clousure');
    telm.setAttribute('title', this._t('Closure'));
    telm.dataset.orgValue = 'open';
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    var selectOpt = document.createElement("option");
    selectOpt.value = "open";
    selectOpt.textContent = this._t("Open");
    telm.appendChild(selectOpt);
    selectOpt = document.createElement("option");
    selectOpt.value = "closed";
    selectOpt.textContent = this._t("Closed");
    telm.appendChild(selectOpt);
    selectOpt = document.createElement("option");
    selectOpt.value = "closed_departure";
    selectOpt.textContent = this._t("C. Departure");
    telm.appendChild(selectOpt);
    selectOpt = document.createElement("option");
    selectOpt.value = "closed_arrival";
    selectOpt.textContent = this._t("C. Arrival");
    telm.appendChild(selectOpt);
    cell.appendChild(telm);

    row = table.insertRow();
    row.setAttribute('name', 'rest_c');

    cell = row.insertCell();
    cell.style.textAlign = 'center';
    cell.setAttribute('colspan', '4');
    telm = document.createElement("button");
    telm.setAttribute('id', this._sanitizeId(`NO_OTA_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'no_ota');
    telm.setAttribute('title', this._t('No OTA'));
    telm.innerHTML = "<strong>No OTA</strong>";
    telm.dataset.orgValue = telm.dataset.state = 'false';
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    telm.classList.add('hcal-management-input', 'pull-left');
    telm.addEventListener('click', function(ev){ $this.onInputChange(ev, this); }, false);
    cell.appendChild(telm);
    telm = document.createElement("span");
    telm.setAttribute('id', this._sanitizeId(`OPTIONS_${roomId}_${dateShortStr}`));
    telm.setAttribute('name', 'options');
    telm.setAttribute('title', this._t('Options'));
    telm.classList.add('dropdown', 'pull-right', 'hcal-management-record-options');
    telm.innerHTML = `
      <a href='#' data-toggle='dropdown' class='dropdown-toggle'><i class='fa fa-2x fa-ellipsis-v'> </i></a>
      <ul class='dropdown-menu' style='min-width: 80px'>
        <li><a href='#' class='hcal-record-option-clone' data-hcal-parent-cell='${parentCell.getAttribute('id')}'>${this._t('Clone')}</a></li>
        <li role='separator' class='divider'></li>
        <li><a href='#' class='hcal-record-option-copy' data-hcal-parent-cell='${parentCell.getAttribute('id')}'>${this._t('Copy')}</a></li>
        <li><a href='#' class='hcal-record-option-paste' data-hcal-parent-cell='${parentCell.getAttribute('id')}'>${this._t('Paste')}</a></li>
        <li role='separator' class='divider'></li>
        <li><a href='#' class='hcal-record-option-reset' data-hcal-parent-cell='${parentCell.getAttribute('id')}'>${this._t('Reset')}</a></li>
      </ul>`;
    telm.dataset.hcalParentCell = parentCell.getAttribute('id');
    cell.appendChild(telm);

    cell.querySelector('.hcal-record-option-clone').addEventListener('click', function(ev){ $this.onOptionsRecord(ev, this); }, false);
    cell.querySelector('.hcal-record-option-reset').addEventListener('click', function(ev){ $this.onOptionsRecord(ev, this); }, false);
    cell.querySelector('.hcal-record-option-copy').addEventListener('click', function(ev){ $this.onOptionsRecord(ev, this); }, false);
    cell.querySelector('.hcal-record-option-paste').addEventListener('click', function(ev){ $this.onOptionsRecord(ev, this); }, false);


    parentCell.appendChild(table);

    return table;
  },

  _getCell: function(/*HRoomObject*/room, /*DateTimeObject*/sdate) {
    return this.e.querySelector(`#${this._sanitizeId(`${room.name}_${room.id}_${sdate.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`)}`);
  },

  setData: function(prices, restrictions, avail, count_free_rooms) {
    //this._updateView();
    if (typeof prices !== 'undefined' && prices) {
      this._pricelist = prices;
      this._updatePriceList();
    }
    if (typeof restrictions !== 'undefined' && restrictions) {
      this._restrictions = restrictions;
      this._updateRestrictions();
    }
    if (typeof avail !== 'undefined' && avail) {
      this.setAvailability(avail);
    }
    if (typeof count_free_rooms !== 'undefined' && count_free_rooms) {
      this._free_rooms = count_free_rooms;
      this._updateNumFreeRooms();
    }
  },

  setAvailability: function(avails) {
    this._availability = avails;
    if (this._availability) {
      for (var elm of this.etable.querySelectorAll("tr[name=avail]")) {
        elm.style.display = "";
      }
    }
    this._updateAvailability();
  },

  //==== ROOMS
  getRoom: function(/*String*/id) {
    return _.find(this.options.rooms, function(item){ return item.id == id; });
  },

  //==== RENDER FUNCTIONS
  _create_table_data_days: function() {
    var $this = this;
    while (this.e.hasChildNodes()) {
  		this.e.removeChild(this.e.lastChild);
  	}

    // RoomType Names
    this.edivrhl = document.createElement("div");
    this.edivrhl.classList.add('table-room_types');
    this.e.appendChild(this.edivrhl);
    this.etableRooms = document.createElement("table");
    this.etableRooms.classList.add('hcal-management-table');
    this.etableRooms.classList.add('noselect');
    this.edivrhl.appendChild(this.etableRooms);

    // Container: Days + Data
    this.edivm = document.createElement("div");
    this.edivm.setAttribute('id', 'hcal-management-container-dd');
    this.e.appendChild(this.edivm);
    // Days
    this.edivrh = document.createElement("div");
    this.edivrh.classList.add('table-room_type-data-header');
    this.edivm.appendChild(this.edivrh);
    this.etableHeader = document.createElement("table");
    this.etableHeader.classList.add('hcal-management-table');
    this.etableHeader.classList.add('noselect');
    this.edivrh.appendChild(this.etableHeader);
    // Data
    this.edivr = document.createElement("div");
    this.edivr.classList.add('table-room_type-data');
    this.edivm.appendChild(this.edivr);
    this.etable = document.createElement("table");
    this.etable.classList.add('hcal-management-table');
    this.etable.classList.add('noselect');
    this.edivr.appendChild(this.etable);

    /** TABLE HEADER **/
    var thead = this.etableHeader.createTHead();

    // Render Next Days
    var row = thead.insertRow();
    var now = moment().local();
    for (var i=0; i<=this.options.days; i++) {
      var dd = this.options.startDate.clone().add(i,'d');
      var dd_local = dd.clone().local();
      var cell = row.insertCell();
      cell.setAttribute('id', this._sanitizeId(`hday_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`));
      cell.classList.add('hcal-cell-header-day');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-3d');
      cell.dataset.hcalDate = dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT);
      cell.textContent = dd.format('D') + ' ' + dd.format('ddd') + ' (' + dd.format('MMM') + "'" + dd.format('YY') + ')';
      cell.setAttribute('title', dd.format('dddd'))
      var day = +dd_local.format('D');
      if (day == 1) {
        cell.classList.add('hcal-cell-start-month');
      }
      if (dd_local.isSame(now, 'day')) {
        cell.classList.add('hcal-cell-current-day');
      } else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
        cell.classList.add('hcal-cell-end-week');
      }
    }

    /** ROOM LINES **/
    var tbody = document.createElement("tbody");
    this.etableRooms.appendChild(tbody);
    this.options.rooms.forEach(function(itemRoom, indexRoom){
      row = tbody.insertRow();
      cell = row.insertCell();
      cell.textContent = itemRoom.name;
      cell.setAttribute('colspan', 2);
      cell.classList.add('hcal-cell-room-type-group-item');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-3d');
    });

    /** ROOM DATA LINES **/
    var tbody = document.createElement("tbody");
    this.etable.appendChild(tbody);
    this.options.rooms.forEach(function(itemRoom, indexRoom){
      // Room Number
      row = tbody.insertRow();
      row.setAttribute('id', $this._sanitizeId(`ROW_${itemRoom.name}_${itemRoom.id}`));
      row.dataset.hcalRoomObjId = itemRoom.id;
      row.classList.add('hcal-row-room-type-group-item');
      for (var i=0; i<=$this.options.days; i++) {
        var dd = $this.options.startDate.clone().add(i,'d');
        var dd_local = dd.clone().local();
        cell = row.insertCell();
        cell.setAttribute('id', $this._sanitizeId(`${itemRoom.name}_${itemRoom.id}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`));
        cell.classList.add('hcal-cell-room-type-group-item-day');
        cell.dataset.hcalParentRow = row.getAttribute('id');
        cell.dataset.hcalDate = dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT);
        // Generate Interactive Table
        cell.appendChild($this._generateTableDay(cell));
        //cell.innerHTML = dd.format("DD");
        var day = +dd_local.format("D");
        if (day == 1) {
          cell.classList.add('hcal-cell-start-month');
        }
        if (dd_local.isSame(now, 'day')) {
          cell.classList.add('hcal-cell-current-day');
        } else if (dd_local.format('e') >= $this.options.endOfWeek-$this.options.endOfWeekOffset && dd_local.format('e') <= $this.options.endOfWeek) {
          cell.classList.add('hcal-cell-end-week');
        }
      }
    });
  },

  //==== PRICELIST
  addPricelist: function(/*Object*/pricelist) {
    var room_type_ids = Object.keys(pricelist);
    for (var vid of room_type_ids) {
      if (vid in this._pricelist) {
        for (var price of pricelist[vid]) {
          var index = _.findIndex(this._pricelist[vid], {date: price['date']});
          if (index >= 0) {
            this._pricelist[vid][index] = price;
          } else {
            this._pricelist[vid].push(price);
          }
        }
      }
      else {
        this._pricelist[vid] = pricelist[vid];
      }
    }
    this._updatePriceList();
  },

  _updatePriceList: function() {
    var keys = Object.keys(this._pricelist);
    for (var room_typeId of keys) {
      for (var price of this._pricelist[room_typeId]) {
        var dd = HotelCalendarManagement.toMoment(price.date, this.options.dateFormatShort);
        var inputId = this._sanitizeId(`PRICE_${room_typeId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`);
        var input = this.etable.querySelector(`#${inputId}`);
        if (input && !input.classList.contains('hcal-management-input-changed')) {
          input.dataset.orgValue = price.price;
          input.value = price.price;
        }
      }
    }
  },

  getPricelist: function(onlyNew) {
    var data = {};
    for (var room of this.options.rooms) {
      for (var i=0; i<=this.options.days; i++) {
        var ndate = this.options.startDate.clone().add(i, 'd');
        var ndateStr = ndate.format(HotelCalendarManagement._DATE_FORMAT_SHORT);
        var inputId = this._sanitizeId(`PRICE_${room.id}_${ndateStr}`);
        var input = this.etable.querySelector(`#${inputId}`);
        if (!onlyNew || (onlyNew && input.value !== input.dataset.orgValue)) {
          if (!(room.id in data)) { data[room.id] = []; }
          data[room.id].push({
            'date': ndate.format('YYYY-MM-DD'),
            'price': input.value
          });
        }
      }
    }
    return data;
  },

  //==== RESTRICTIONS
  addRestrictions: function(/*Object*/restrictions) {
    var room_type_ids = Object.keys(restrictions);
    for (var vid of room_type_ids) {
      if (vid in this._restrictions) {
        for (var rest of restrictions[vid]) {
          var index = _.findIndex(this._restrictions[vid], {date: rest['date']});
          if (index >= 0) {
            this._restrictions[vid][index] = rest;
          } else {
            this._restrictions[vid].push(rest);
          }
        }
      }
      else {
        this._restrictions[vid] = restrictions[vid];
      }
    }
    this._updateRestrictions();
  },

  _updateRestrictions: function() {
    var keys = Object.keys(this._restrictions);
    for (var room_typeId of keys) {
      var room = this.getRoom(room_typeId);
      for (var restriction of this._restrictions[room_typeId]) {
        var dd = HotelCalendarManagement.toMoment(restriction.date, this.options.dateFormatShort);
        var inputIds = [
          this._sanitizeId(`MIN_STAY_${room_typeId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`), restriction.min_stay,
          this._sanitizeId(`MIN_STAY_ARRIVAL_${room_typeId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`), restriction.min_stay_arrival,
          this._sanitizeId(`MAX_STAY_${room_typeId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`), restriction.max_stay,
          this._sanitizeId(`MAX_STAY_ARRIVAL_${room_typeId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`), restriction.max_stay_arrival,
        ];
        for (var i=0; i<inputIds.length; i+=2) {
          var inputItem = this.etable.querySelector(`#${inputIds[i]}`);
          if (inputItem && !inputItem.classList.contains('hcal-management-input-changed')) {
            inputItem.dataset.orgValue = inputItem.value = inputIds[i+1];
            inputItem.style.backgroundColor = inputIds[i+1]!=0?'#f9d70b':'';
          }
        }

        var inputClousureId = this._sanitizeId(`CLOUSURE_${room_typeId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`);
        var inputClousure = this.etable.querySelector(`#${inputClousureId}`);
        if (inputClousure && !inputClousure.classList.contains('hcal-management-input-changed')) {
          inputClousure.dataset.orgValue = inputClousure.value = (restriction.closed && 'closed') ||
                                                          (restriction.closed_arrival && 'closed_arrival') ||
                                                          (restriction.closed_departure && 'closed_departure') || 'open';
        }
      }
    }
  },

  getRestrictions: function(onlyNew) {
    var data = {};
    for (var room of this.options.rooms) {
      for (var i=0; i<=this.options.days; i++) {
        var ndate = this.options.startDate.clone().add(i, 'd');
        var ndateStr = ndate.format(HotelCalendarManagement._DATE_FORMAT_SHORT);
        var inputMinStayId = this._sanitizeId(`MIN_STAY_${room.id}_${ndateStr}`);
        var inputMinStay = this.etable.querySelector(`#${inputMinStayId}`);
        var inputMinStayArrivalId = this._sanitizeId(`MIN_STAY_ARRIVAL_${room.id}_${ndateStr}`);
        var inputMinStayArrival = this.etable.querySelector(`#${inputMinStayArrivalId}`);
        var inputMaxStayId = this._sanitizeId(`MAX_STAY_${room.id}_${ndateStr}`);
        var inputMaxStay = this.etable.querySelector(`#${inputMaxStayId}`);
        var inputMaxStayArrivalId = this._sanitizeId(`MAX_STAY_ARRIVAL_${room.id}_${ndateStr}`);
        var inputMaxStayArrival = this.etable.querySelector(`#${inputMaxStayArrivalId}`);
        var inputClousureId = this._sanitizeId(`CLOUSURE_${room.id}_${ndateStr}`);
        var inputClousure = this.etable.querySelector(`#${inputClousureId}`);

        if (!onlyNew || (onlyNew && (inputMinStay.value !== inputMinStay.dataset.orgValue ||
                                      inputMinStayArrival.value !== inputMinStayArrival.dataset.orgValue ||
                                      inputMaxStay.value !== inputMaxStay.dataset.orgValue ||
                                      inputMaxStayArrival.value !== inputMaxStayArrival.dataset.orgValue ||
                                      inputClousure.value !== inputClousure.dataset.orgValue))) {
          if (!(room.id in data)) { data[room.id] = []; }
          data[room.id].push({
            'date': ndate.format('YYYY-MM-DD'),
            'min_stay': inputMinStay.value,
            'min_stay_arrival': inputMinStayArrival.value,
            'max_stay': inputMaxStay.value,
            'max_stay_arrival': inputMaxStayArrival.value,
            'closed': inputClousure.value === 'closed',
            'closed_arrival': inputClousure.value === 'closed_arrival',
            'closed_departure': inputClousure.value === 'closed_departure'
          });
        }
      }
    }
    return data;
  },

  //==== FREE Rooms
  _updateNumFreeRooms: function() {
    var keys = Object.keys(this._free_rooms);
    for (var room_typeId of keys) {
      for (var fnroom of this._free_rooms[room_typeId]) {
        var dd = HotelCalendarManagement.toMoment(fnroom.date, this.options.dateFormatShort);
        var inputIds = [
          `FREE_ROOMS_${room_typeId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`, fnroom.num,
        ];

        for (var i=0; i<inputIds.length; i+=2) {
          var inputId = this._sanitizeId(inputIds[i]);
          var input = this.etable.querySelector(`#${inputId}`);
          if (input) {
            input.dataset.orgValue = input.value = inputIds[i+1];
          }
        }
      }
    }
  },

  //==== AVAILABILITY
  addAvailability: function(/*Object*/availability) {
    var room_type_ids = Object.keys(availability);
    for (var vid of room_type_ids) {
      if (vid in this._availability) {
        for (var avail of availability[vid]) {
          var index = _.findIndex(this._availability[vid], {date: avail['date']});
          if (index >= 0) {
            this._availability[vid][index] = avail;
          } else {
            this._availability[vid].push(avail);
          }
        }
      }
      else {
        this._availability[vid] = availability[vid];
      }
    }
    this._updateAvailability();
  },

  _updateAvailability: function() {
    var keys = Object.keys(this._availability);
    for (var room_typeId of keys) {
      for (var avail of this._availability[room_typeId]) {
        var dd = HotelCalendarManagement.toMoment(avail.date, this.options.dateFormatShort);
        var inputIds = [
          `QUOTA_${room_typeId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`, avail.quota,
          `MAX_AVAIL_${room_typeId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`, avail.max_avail,
          `CHANNEL_AVAIL_${room_typeId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`, avail.channel_avail,
          `NO_OTA_${room_typeId}_${dd.format(HotelCalendarManagement._DATE_FORMAT_SHORT)}`, avail.no_ota
        ];
        for (var i=0; i<inputIds.length; i+=2) {
          var inputId = this._sanitizeId(inputIds[i]);
          var input = this.etable.querySelector(`#${inputId}`);
          if (input && !input.classList.contains('hcal-management-input-changed')) {
            input.dataset.orgValue = inputIds[i+1];
            if (input.tagName.toLowerCase() === 'button') {
              input.dataset.state = inputIds[i+1];
              input.textContent = inputIds[i+1]?"No OTA!":"No OTA";
              if (inputIds[i+1]) {
                input.classList.add('hcal-management-input-active');
              }
              else {
                input.classList.remove('hcal-management-input-active');
              }
            }
            else {
              input.value = inputIds[i+1];
              input.style.backgroundColor = (input.name === 'channel_avail' && input.value == 0)?'rgb(255, 174, 174)':'';
              // input.style.color = (input.name === 'quota' && input.value == 0)?'rgb(255, 174, 174)':'';
            }
          }
        }
      }
    }
  },

  getAvailability: function(onlyNew) {
    var data = {};
    for (var room of this.options.rooms) {
      for (var i=0; i<=this.options.days; i++) {
        var ndate = this.options.startDate.clone().add(i, 'd');
        var ndateStr = ndate.format(HotelCalendarManagement._DATE_FORMAT_SHORT);
        var inputQuotaId = this._sanitizeId(`QUOTA_${room.id}_${ndateStr}`);
        var inputQuota = this.etable.querySelector(`#${inputQuotaId}`);
        var inputMaxAvailId = this._sanitizeId(`MAX_AVAIL_${room.id}_${ndateStr}`);
        var inputMaxAvail = this.etable.querySelector(`#${inputMaxAvailId}`);
        var inputNoOTAId = this._sanitizeId(`NO_OTA_${room.id}_${ndateStr}`);
        var inputNoOTA = this.etable.querySelector(`#${inputNoOTAId}`);
        var inputChannelAvailId = this._sanitizeId(`CHANNEL_AVAIL_${room.id}_${ndateStr}`);
        var inputChannelAvail = this.etable.querySelector(`#${inputChannelAvailId}`);

        if (!onlyNew || (onlyNew && (inputQuota.value !== inputQuota.dataset.orgValue
                                      || inputMaxAvail.value !== inputMaxAvail.dataset.orgValue
                                      || (inputNoOTA.dataset.state && inputNoOTA.dataset.state !== inputNoOTA.dataset.orgValue)))) {
          if (!(room.id in data)) { data[room.id] = []; }
          data[room.id].push({
            'date': ndate.format('YYYY-MM-DD'),
            'quota': inputQuota.value,
            'max_avail': inputMaxAvail.value,
            'no_ota': Boolean(inputNoOTA.dataset.state === 'true') || false,
            'channel_avail': inputChannelAvail.value,
          });
        }
      }
    }
    return data;
  },

  //==== UPDATE FUNCTIONS
  _updateView: function() {
    this._create_table_data_days();
    this.setMode();
  },

  //==== HELPER FUNCTIONS
  getDateDiffDays: function(/*MomentObject*/start, /*MomentObject*/end) {
	  return end.clone().startOf('day').diff(start.clone().startOf('day'), 'days');
  },

  _t: function(/*String*/str) {
    if (str in this._strings) {
      return this._strings[str];
    }
    return str;
  },

  _sanitizeId: function(/*String*/str) {
    return str.replace(/[^a-zA-Z0-9\-_]/g, '_');
  },

  _isNumeric: function(/*?*/n) {
    return !isNaN(parseFloat(n)) && isFinite(n);
  },

  //==== EVENT FUNCTIONS
  onInputChange: function(/*EventObject*/ev, /*HTMLObject*/elm) {
    var parentCell = this.$base.querySelector(`#${elm.dataset.hcalParentCell}`);
    var parentRow = this.$base.querySelector(`#${parentCell.dataset.hcalParentRow}`);
    var dateCell = HotelCalendarManagement.toMoment(parentCell.dataset.hcalDate);
    var room = this.getRoom(parentRow.dataset.hcalRoomObjId);
    var name = elm.getAttribute('name');
    var value = elm.value;
    var orgValue = elm.dataset.orgValue;

    if (elm.getAttribute('type') === 'checkbox') {
      value = elm.checked;
    }
    else if (name === 'min_stay' || name === 'min_stay_arrival' || name === 'max_stay' ||
              name === 'price' || name === 'quota' || name === 'max_avail' || name === 'max_stay_arrival') {
      if (!this._isNumeric(value)) {
        elm.style.backgroundColor = 'red';
      } else if (orgValue !== value) {
        elm.classList.add('hcal-management-input-changed');
        elm.style.backgroundColor = '';
      } else {
        elm.classList.remove('hcal-management-input-changed');
        if (name === 'avail' && value == 0) {
          elm.style.backgroundColor = 'rgb(255, 174, 174)';
        } else if (value != 0 && (name === 'min_stay' || name === 'max_stay' || name === 'min_stay_arrival' || name === 'max_stay_arrival')) {
          elm.style.backgroundColor = '#f9d70b';
        }
      }
    }
    else if (name === 'clousure') {
      if (orgValue !== value) {
        elm.classList.add('hcal-management-input-changed');
      } else {
        elm.classList.remove('hcal-management-input-changed');
      }
    }
    else if (elm.tagName.toLowerCase() === 'button') {
      value = Boolean(!(elm.dataset.state === 'true'));
      elm.dataset.state = value;
      if (name === 'no_ota') {
        elm.textContent = value?'No OTA!':'No OTA';
        if (value) {
          elm.classList.add('hcal-management-input-active');
        } else {
          elm.classList.remove('hcal-management-input-active');
        }

        if (value.toString() !== orgValue) {
          elm.classList.add('hcal-management-input-changed');
        } else {
          elm.classList.remove('hcal-management-input-changed');
        }
      }
    }

    var hasInputChanged = parentCell.querySelector('.hcal-management-input-changed');
    if (hasInputChanged) {
      parentCell.classList.add('hcal-management-record-changed');
    } else {
      parentCell.classList.remove('hcal-management-record-changed');
    }

    this.e.dispatchEvent(new CustomEvent(
      'hcmOnInputChanged',
      {'detail': {'date': dateCell, 'room': room, 'name': name, 'value': value}}));
  },

  onOptionsRecord: function(/*EventObject*/ev, /*HTMLObject*/elm) {
    var $this = this;
    var parentCell = this.$base.querySelector(`#${elm.dataset.hcalParentCell}`);
    var parentRow = this.$base.querySelector(`#${parentCell.dataset.hcalParentRow}`);
    var dateCell = HotelCalendarManagement.toMoment(parentCell.dataset.hcalDate);
    var room = this.getRoom(parentRow.dataset.hcalRoomObjId);

    var copy_values = {};
    var inputs = parentCell.querySelectorAll(".hcal-management-input");
    for (var cinput of inputs) {
      var name = cinput.getAttribute('name');

      if (name === 'no_ota') {
        copy_values[name] = cinput.dataset.state;
      } else {
        copy_values[name] = cinput.value;
      }
    }

    var eventChange = new UIEvent('change', {
      'view': window,
      'bubbles': true,
      'cancelable': true
    });
    var eventClick = new UIEvent('click', {
      'view': window,
      'bubbles': true,
      'cancelable': true
    });

    if (elm.classList.contains('hcal-record-option-clone')) {
      var dialog = bootbox.dialog({
        size: 'medium',
        title: "Clone " + parentCell.dataset.hcalDate + " values in '" + room.name + "' room",
        message: `
          <table style="margin: 0 auto" id="hcal-management-clone-dates">
              <tbody>
                  <tr>
                      <td colspan='2'>
                        <div class="well">
                          <b>Price:</b> ${copy_values['price']}<br/>
                          <b>Availability:</b> ${copy_values['avail']}<br/>
                          <b>Min. Stay:</b> ${copy_values['min_stay']}<br/>
                          <b>Max. Stay:</b> ${copy_values['max_stay']}<br/>
                          <b>Min. Stay Arrival:</b> ${copy_values['min_stay_arrival']}<br/>
                          <b>Max. Stay Arrival:</b> ${copy_values['max_stay_arrival']}<br/>
                          <b>Clousure:</b> ${copy_values['clousure']}<br/>
                          <b>No OTA:</b> ${copy_values['no_ota']}<br/>
                        </div>
                      </td>
                  </tr>
                  <tr>
                      <td>
                          FROM<br/>
                          <div class="input-group date" id="date_begin">
                              <input type="text" class="form-control" name="date_begin" required="required" readonly="1"/>
                              <span class="input-group-addon">
                                  <span class="fa fa-calendar"></span>
                              </span>
                          </div>
                      </td>
                      <td>
                          TO<br/>
                          <div class="input-group date" id="date_end">
                              <input type="text" class="form-control" name="date_end" required="required" readonly="1"/>
                              <span class="input-group-addon">
                                  <span class="fa fa-calendar"></span>
                              </span>
                          </div>
                      </td>
                  </tr>
                  <tr>
                    <td colspan="2">
                      <input type="checkbox" id="same_day" />
                      <label for="same_day">Same day of week</label>
                    </td>
                  </tr>
              </tbody>
          </table>`,
        buttons: {
          confirm : {
            label: $this._t('Clone'),
            className: "btn-success",
            callback: function() {
              var date_begin = $('table#hcal-management-clone-dates #date_begin').data("DateTimePicker").getDate().set({'hour': 0, 'minute': 0, 'second': 0}).clone();
              var date_end = $('table#hcal-management-clone-dates #date_end').data("DateTimePicker").getDate().set({'hour': 0, 'minute': 0, 'second': 0}).clone();
              var diff_days = $this.getDateDiffDays(date_begin, date_end) + 1;
              var same_day = $('table#hcal-management-clone-dates #same_day').is(':checked');
              var cell_date = HotelCalendarManagement.toMoment(parentCell.dataset.hcalDate);

              var ndate = date_begin.clone();
              for (var i=0; i<diff_days; ++i) {
                if (same_day && ndate.weekday() !== cell_date.weekday()) {
                  ndate.add(1, 'd');
                  continue;
                }
                var cell = $this._getCell(room, ndate);

                var inputs = cell.querySelectorAll(".hcal-management-input");
                for (var cinput of inputs) {
                  var name = cinput.getAttribute('name');

                  if (name === 'no_ota') {
                    cinput.dataset.state = Boolean(!(copy_values[name] === 'true'));
                    cinput.dispatchEvent(eventClick);
                  } else {
                    cinput.value = copy_values[name];
                    cinput.dispatchEvent(eventChange);
                  }
                }
                ndate.add(1, 'd');
              }
            }
          },
          cancel: {
            label: $this._t('Cancel'),
            className: 'btn-danger'
          }
        }
      });
      dialog.init(function(){
        var DTPickerOptions = {
          icons : {
            time: 'fa fa-clock-o',
            date: 'fa fa-calendar',
            up: 'fa fa-chevron-up',
            down: 'fa fa-chevron-down'
          },
          minDate: $this.options.startDate,
          maxDate: $this.options.startDate.clone().add($this.options.days, 'd'),
          //language : moment.locale(),
          format : HotelCalendarManagement._DATE_FORMAT_SHORT,
          disabledHours: [0, 1, 2, 3, 4, 5, 6, 7, 8, 18, 19, 20, 21, 22, 23]
        };

        $('table#hcal-management-clone-dates #date_begin').datetimepicker(DTPickerOptions);
        $('table#hcal-management-clone-dates #date_end').datetimepicker(DTPickerOptions);
      });
    }
    else if (elm.classList.contains('hcal-record-option-reset')) {
      var inputs = parentCell.querySelectorAll(".hcal-management-input");
      for (var cinput of inputs) {
        var need_dispatch = false;
        var name = cinput.getAttribute('name');
        if (name === "min_stay" || name === "max_stay" || name === "min_stay_arrival" || name === "max_stay_arrival" ||
              name === "avail" || name === "price" || name === "clousure") {
          cinput.value = (name === "clousure")?cinput.dataset.orgValue:parseInt(cinput.dataset.orgValue, 10);
          cinput.dispatchEvent(eventChange);
        }
        else if (name === 'no_ota') {
          cinput.dataset.state = Boolean(!(cinput.dataset.orgValue === 'true'));
          cinput.dispatchEvent(eventClick);
        }
      }
    }
    else if (elm.classList.contains('hcal-record-option-copy')) {
      this._copy_values = {};
      var inputs = parentCell.querySelectorAll(".hcal-management-input");
      for (var cinput of inputs) {
        var name = cinput.getAttribute('name');

        if (name === 'no_ota') {
          this._copy_values[name] = cinput.dataset.state;
        } else {
          this._copy_values[name] = cinput.value;
        }
      }
    }
    else if (elm.classList.contains('hcal-record-option-paste')) {
      if (_.isEmpty(this._copy_values)) {
        return;
      }

      var eventChange = new UIEvent('change', {
        'view': window,
        'bubbles': true,
        'cancelable': true
      });
      var eventClick = new UIEvent('click', {
        'view': window,
        'bubbles': true,
        'cancelable': true
      });

      var inputs = parentCell.querySelectorAll(".hcal-management-input");
      for (var cinput of inputs) {
        var name = cinput.getAttribute('name');

        if (name === 'no_ota') {
          cinput.dataset.state = Boolean(!(this._copy_values[name] === 'true'));
          cinput.dispatchEvent(eventClick);
        } else {
          cinput.value = this._copy_values[name];
          cinput.dispatchEvent(eventChange);
        }
      }
    }
  }
};

/** STATIC METHODS **/
HotelCalendarManagement.MODE = { NONE:0, COPY:1, PASTE:2, ALL:3, MEDIUM:4, LOW:5 };
HotelCalendarManagement._DATE_FORMAT_LONG = "DD/MM/YYYY HH:mm:ss";
HotelCalendarManagement._DATE_FORMAT_SHORT = "DD/MM/YYYY";
HotelCalendarManagement.toMoment = function(/*String,MomentObject*/ndate, /*String*/format) {
  if (moment.isMoment(ndate)) {
    return ndate;
  } else if (typeof ndate === 'string' || ndate instanceof Date) {
    ndate = moment(ndate, typeof format==='undefined'?HotelCalendarManagement._DATE_FORMAT_LONG:format);
    if (moment.isMoment(ndate)) {
      return ndate;
    }
  }
  console.warn('[Hotel Calendar][toMoment] Invalid date format!');
  return false;
}


/** ROOM OBJECT **/
function HRoomType(/*Int*/id, /*String*/name, /*Int*/capacity, /*Float*/price) {
  this.id = id || -1;
  this.name = name;
  this.capacity = capacity;
  this.price = price;

  this.userData_ = {};
}
HRoomType.prototype = {
  clearUserData: function() { this.userData_ = {}; },
  getUserData: function(/*String?*/key) {
    if (typeof key === 'undefined') {
      return this.userData_;
    }
    return this.userData_[key];
  },
  addUserData: function(/*Dictionary*/data) {
    if (!_.isObject(data)) {
      console.warn("[Hotel Calendar Management][HRoomType][setUserData] Invalid Data! Need be a object!");
    } else {
      this.userData_ = _.extend(this.userData_, data);
    }
  },
};
