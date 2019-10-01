/* global _, moment */
'use strict';
/*
 * Hotel Calendar JS - 2017-2018
 * GNU Public License
 * Alexandre Díaz <dev@redneboa.es>
 *
 * Dependencies:
 *     - moment
 *     - underscore
 *     - awesomeicons
 *     - bootstrap
 *     - jquery
 */

function HotelCalendar(/*String*/querySelector, /*Dictionary*/options, /*List*/pricelist, /*restrictions*/restrictions, /*HTMLObject?*/_base) {
  if (window === this) {
    return new HotelCalendar(querySelector, options, pricelist, _base);
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
      Version: '0.5',
      Author: "Alexandre Díaz",
      Created: "20/04/2017",
      Updated: "19/07/2018"
    };
  }

  /** Strings **/
  this._strings = {
    'Save Changes': 'Save Changes'
  };

  /** Options **/
  var now_utc = moment(new Date()).utc();
  this.options = _.extend({
    startDate: now_utc,
    days: now_utc.daysInMonth(),
    rooms: [],
    room_types: [],
    room_classes: [],
    allowInvalidActions: false,
    assistedMovement: false,
    endOfWeek: 6,
    endOfWeekOffset: 0,
    divideRoomsByCapacity: false,
    currencySymbol: '€',
    showPricelist: false,
    showAvailability: false,
    showNumRooms: 0,
    paginatorStepsMin: 1,
    paginatorStepsMax: 15,
    showOverbookings: false,
    showCancelled: false,
  }, options);

  this.options.startDate = this.options.startDate.clone();
  this.options.startDate.subtract('1', 'd');
  this.options.orig_days = this.options.days;
  this.options.days = this.parseDays(this.options.days) + 1;
  this.options.rooms = _.map(this.options.rooms, function(item){ return item.clone(); });
  // Check correct values
  if (this.options.rooms.length > 0 && !(this.options.rooms[0] instanceof HRoom)) {
    this.options.rooms = [];
    console.warn("[Hotel Calendar][init] Invalid Room definiton!");
  }

  /** Internal Values **/
  this._pricelist = pricelist || []; // Store Prices
  this._pricelist_id = -1;  // Store Price Plan ID (Because can be edited)
  this._restrictions = restrictions || {}; // Store Restrictions
  this._reservations = [];  // Store Reservations
  this._reservationsMap = {}; // Store Reservations Mapped by Room for Search Purposes
  this._modeSwap = HotelCalendar.MODE.NONE; // Store Swap Mode
  this._selectionMode = HotelCalendar.MODE.NONE;
  this._endDate = this.options.startDate.clone().add(this.options.days, 'd'); // Store End Calendar Day
  this._tableCreated = false; // Store Flag to Know Calendar Creation
  this._cellSelection = {start:false, end:false, current:false}; // Store Info About Selected Cells
  this._lazyModeReservationsSelection = false; // Store Info About Timer for Selection Action
  this._domains = {}; // Store domains for filter rooms & reservations
  this._divideDivs = false;
  this._extraRowIndicators = ['EX-', '/#'];

  // Support
  var self = this;
  this._supportsPassive = false;
  try {
    var opts = Object.defineProperty({}, 'passive', {
      get: function() {
        self._supportsPassive = true;
      }
    });
    window.addEventListener("testPassive", null, opts);
    window.removeEventListener("testPassive", null, opts);
  } catch (e) {}

  // Calculate Capacities
  this._roomCapacityTotal = 0;
  this._roomCapacities = {};
  this._roomsMap = _.groupBy(this.options.rooms, 'type');
  var room_types = this.getRoomTypes();
  for (var rt of room_types) {
    this._roomsMap[rt] = _.filter(this._roomsMap[rt], {overbooking: false, cancelled: false});
    this._roomCapacities[rt] = _.reduce(this._roomsMap[rt], function(memo, tr){ return memo + (tr.shared?tr.capacity:1); }, 0);
    this._roomCapacityTotal += this._roomCapacities[rt];
  }

  /***/
  this._reset_action_reservation();
  if (!this._create()) {
    return false;
  }


  /** Main Events **/
  document.addEventListener('mouseup', this.onMainMouseUp.bind(this), false);
  document.addEventListener('touchend', this.onMainMouseUp.bind(this), false);
  document.addEventListener('keyup', this.onMainKeyUp.bind(this), false);
  document.addEventListener('keydown', this.onMainKeyDown.bind(this), false);
  window.addEventListener('resize', _.debounce(this.onMainResize.bind(this), 300), false);

  return this;
}

HotelCalendar.prototype = {
  /** PUBLIC MEMBERS **/
  addEventListener: function(/*String*/event, /*Function*/callback) {
    this.e.addEventListener(event, callback);
  },

  //==== CALENDAR
  setStartDate: function(/*String,MomentObject*/date, /*Int*/days, /*Bool*/fullUpdate, /*Functions*/callback) {
    if (moment.isMoment(date)) {
      this.options.startDate = date;
    } else if (typeof date === 'string'){
      this.options.startDate = HotelCalendar.toMoment(date);
    } else {
      console.warn("[Hotel Calendar][setStartDate] Invalid date format!");
      return;
    }

    this.options.startDate.subtract('1','d');
    if (typeof days !== 'undefined') {
      this.options.orig_days = days;
      this.options.days = this.parseDays(days) + 1;
    }
    this._endDate = this.options.startDate.clone().add(this.options.days, 'd');

    /*this.e.dispatchEvent(new CustomEvent(
            'hcOnChangeDate',
            {'detail': {'prevDate':curDate, 'newDate': $this.options.startDate}}));*/
    this._updateView(!fullUpdate, callback);
  },

  getOptions: function(/*String?*/key) {
    if (typeof key !== 'undefined') {
      return this.options[key];
    }
    return this.options;
  },

  parseDays: function(/*Int/String*/days) {
    if (days === 'month') {
      return moment().daysInMonth();
    }
    return +days;
  },

  toggleOverbookingsVisibility: function(/*Bool*/show) {
    this.options.showOverbookings = !this.options.showOverbookings;
  },

  toggleCancelledVisibility: function(/*Bool*/show) {
    this.options.showCancelled = !this.options.showCancelled;
  },

  setSwapMode: function(/*Int*/mode) {
    if (mode !== this._modeSwap) {
      this._modeSwap = mode;
      if (this._modeSwap === HotelCalendar.MODE.NONE) {
        this._dispatchSwapReservations();
        this._reset_action_reservation();
      } else {
        this.setSelectionMode(HotelCalendar.MODE.NONE);
      }

      this._updateHighlightSwapReservations();
    }
  },

  setSelectionMode: function(/*Int*/mode) {
    if (this._modeSwap === HotelCalendar.MODE.NONE) {
      this._selectionMode = mode;
      if (this._selectionMode === HotelCalendar.ACTION.DIVIDE) {
        this.reservationAction.action = HotelCalendar.ACTION.DIVIDE;
        for (var reserv of this._reservations) {
          reserv._html.classList.add('hcal-reservation-to-divide');
        }
      } else if (this._selectionMode === HotelCalendar.ACTION.UNIFY) {
        this.reservationAction.action = HotelCalendar.ACTION.UNIFY;
        this.reservationAction.toUnify = [];
      } else {
        for (var reserv of this._reservations) {
          reserv._html.classList.remove('hcal-reservation-to-divide');
        }
        if (this._divideDivs) {
          this._divideDivs[0].remove();
          this._divideDivs[1].remove();
          this._divideDivs = false;
        }


        this._dispatchUnifyReservations();
        this._reset_action_reservation();
        this._updateHighlightUnifyReservations();
      }

      this._dispatchEvent('hcalOnChangeSelectionMode', {
        'newMode': this._selectionMode,
      });
    }
  },

  getSelectionMode: function() {
    return this._selectionMode;
  },

  getSwapMode: function() {
    return this._modeSwap;
  },

  cancelSwap: function() {
    if (this._modeSwap !== HotelCalendar.MODE.NONE) {
      this._modeSwap = HotelCalendar.MODE.NONE;
      this._dispatchEvent('hcalOnCancelSwapReservations');
      this._reset_action_reservation();
      this._updateHighlightSwapReservations();
    }
  },

  _updateOffsets: function() {
    this._etableOffset = this.loopedOffsetOptimized(this.etable);
    this._eOffset = this.loopedOffsetOptimized(this.e);
    this._edivrOffset = this.loopedOffsetOptimized(this.edivr);
  },

  //==== DOMAINS
  setDomain: function(/*Int*/section, /*Array*/domain) {
    if (this._domains[section] !== domain) {
      this._domains[section] = domain;
      if (section === HotelCalendar.DOMAIN.RESERVATIONS) {
        this._filterReservations();
      } else if (section === HotelCalendar.DOMAIN.ROOMS) {
        this._filterRooms();
      }
    }
  },

  getDomain: function(/*Int*/section) {
    return this._domains[section] || [];
  },

  //==== RESERVATIONS
  _filterReservations: function() {
    for (var r of this._reservations) {
      r._active = this._in_domain(r, this._domains[HotelCalendar.DOMAIN.RESERVATIONS]);
      this._updateReservation(r, true);
    }

    //_.defer(function(){ this._updateReservationOccupation() }.bind(this));
  },

  getReservationAction: function() {
    return this.reservationAction;
  },

  getReservation: function(/*Int,String*/id) {
    return _.find(this._reservations, function(item){ return item.id == id; });
  },

  // getReservationDiv: function(/*HReservationObject*/reservationObj) {
  //   var reservDiv = this.e.querySelector(`div.hcal-reservation[data-hcal-reservation-obj-id='${reservationObj.id}']`);
  //   return reservDiv;
  // },

  setReservations: function(/*List*/reservations) {
    for (var reservation of this._reservations) {
      this.removeReservation(reservation);
    }

    this._reservations = [];
    this.addReservations(reservations);
  },

  addReservations: function(/*List*/reservations) {
    reservations = reservations || [];

    if (reservations.length > 0 && !(reservations[0] instanceof HReservation)) {
      console.warn("[HotelCalendar][addReservations] Invalid Reservation definition!");
    } else {
      var isCalendarEmpty = (this._reservations.length>0);
      // Merge
      var addedReservations = [];
      for (var r of reservations) {
        var rindex = _.findKey(this._reservations, {'id': r.id});
        if ((!this.options.showOverbookings && r.overbooking) || (!this.options.showCancelled && r.cancelled)) {
          if (rindex) {
            this.removeReservation(this._reservations[rindex]);
          }
          continue;
        }

        var hasCreatedExtraRows = false;
        r = r.clone(); // HOT-FIX: Multi-Calendar Support
        r.room = this.getRoom(r.room_id, r.overbooking || r.cancelled, r.id);
        // need create a overbooking row?
        if (!r.room) {
          if (r.overbooking || r.cancelled) {
            r.room = this.createExtraRoom(this.getRoom(r.room_id), r.id, {
              overbooking: r.overbooking,
              cancelled: r.cancelled,
            });
            this.createExtraRoomRow(r.room);
            hasCreatedExtraRows = true;
          } else {
            console.warn(`Can't found the room '${r.room_id}' for the reservation '${r.id}' (${r.title})!`);
            continue;
          }
        }

        if (rindex) {
          var reserv = this._reservations[rindex];
          r._html = reserv._html;
          if ((reserv.overbooking && !r.overbooking) || (reserv.cancelled && !r.cancelled)) {
            if (this.getReservationsByRoom(reserv.room).length === 1) {
              this.removeExtraRoomRow(reserv);
            }
          }
          this._reservations[rindex] = r;
          if (!r.unusedZone) {
            this._cleanUnusedZones(r);
          }
        } else {
          this._reservations.push(r);
        }

        addedReservations.push(r);
      }

      // Create & Render New Reservations
      _.defer(function(reservs){
        // Update offsets (New Rooms change positions?)
        this._updateOffsets();

        var unusedZones = this._createUnusedZones(reservs);
        // Add Unused Zones
        this._reservations = this._reservations.concat(unusedZones);
        // Create Map
        this._updateReservationsMap();

        var toAssignEvents = [];
        reservs = reservs.concat(unusedZones);
        for (var r of reservs) {
          r._active = this._in_domain(r, this._domains[HotelCalendar.DOMAIN.RESERVATIONS]);
          this._calcReservationCellLimits(r);
          if (r._html) {
            r._html.innerText = r.title;
          } else if (r._limits.isValid()) {
            r._html = document.createElement('div');
            r._html.dataset.hcalReservationObjId = r.id;
            r._html.classList.add('hcal-reservation');
            r._html.classList.add('noselect');
            r._html.innerText = r.title;
            this.edivr.appendChild(r._html);

            if (r.unusedZone) {
            	r._html.classList.add('hcal-unused-zone');
            } else {
              toAssignEvents.push(r._html);
            }
          }
          this._updateReservation(r);
        }

        this._assignReservationsEvents(toAssignEvents);
      }.bind(this), addedReservations);

      _.defer(function(){ this._updateReservationOccupation(); }.bind(this));
    }
  },

  removeReservation: function(/*HReservationObject*/reserv) {
    if (reserv) {
      // Remove all related content...
      var elms = [reserv._html, this.e.querySelector(`.hcal-warn-ob-indicator[data-hcal-reservation-obj-id='${reserv.id}']`)];
      for (var elm of elms) {
        if (elm && elm.parentNode) {
          elm.parentNode.removeChild(elm);
        }
      }
      // Remove OB Row
      if (reserv.overbooking || reserv.cancelled) {
        if (this.getReservationsByRoom(reserv.room).length === 1) {
          this.removeExtraRoomRow(reserv);
        }
      }
      // Remove Unused Zones
      if (!reserv.unusedZone) {
        this._cleanUnusedZones(reserv);
      }

      this._reservations = _.reject(this._reservations, {id: reserv.id});
      this._updateReservationsMap();
    } else {
      console.warn(`[HotelCalendar][removeReservation] Can't remove '${reserv.id}' reservation!`);
    }
  },

  getReservationsByDay: function(/*MomentObject*/day, /*Bool?*/noCheckouts, /*Bool?*/includeUnusedZones, /*Int?*/nroom, /*Int?*/nbed, /*HReservation?*/ignoreThis) {
    var inclusivity = noCheckouts?'[)':'[]';

    if (typeof nroom !== 'undefined') {
      return _.filter(this._reservationsMap[nroom], function(item){
        return day.isBetween(item.startDate, item.endDate, 'day', inclusivity) &&
                (typeof nbed === 'undefined' || item._beds.includes(nbed)) &&
                ((includeUnusedZones && item.unusedZone) || !item.unusedZone) &&
                item !== ignoreThis && !item.overbooking && !item.cancelled;
      });
    } else {
      return _.filter(this._reservations, function(item){
        return day.isBetween(item.startDate, item.endDate, 'day', inclusivity) &&
                (typeof nbed === 'undefined' || item._beds.includes(nbed)) &&
                ((includeUnusedZones && item.unusedZone) || !item.unusedZone) &&
                item !== ignoreThis && !item.overbooking && !item.cancelled;
      });
    }
  },

  getReservationsByRoom: function(/*Int,HRoomObject*/room, /*Boolean*/includeUnusedZones) {
    if (!(room instanceof HRoom)) { room = this.getRoom(room); }
    if (room) {
      return _.filter(this._reservationsMap[room.id], function(item){
        return (includeUnusedZones || (!includeUnusedZones && !item.unusedZone));
      });
    }

    return [];
  },

  _updateReservationsMap: function() {
    this._reservationsMap = {};
    this._reservations.map(function(current){
      if (!(current.room.id in this._reservationsMap)) {
        this._reservationsMap[current.room.id] = [];
      }
      this._reservationsMap[current.room.id].push(current);
    }.bind(this));
  },

  _calcReservationCellLimits: function(/*HReservationObject*/reservation, /*Int?*/nbed, /*Bool?*/notCheck) {
    var limits = new HLimit();
    if (!reservation.startDate || !reservation.endDate ||
        (!reservation.startDate.isBetween(this.options.startDate, this._endDate, 'day', '[]') &&
         !reservation.endDate.isBetween(this.options.startDate, this._endDate, 'day', '[]') &&
         !reservation.startDate.isBefore(this.options.startDate, 'day', '()') &&
         !reservation.endDate.isAfter(this._endDate, 'day', '()'))) {
      return limits;
    }

    var notFound;
    do {
      notFound = false;

      // Num of beds
      var bedNum;
      if (typeof nbed === 'undefined') {
        if (reservation._beds && reservation._beds.length) {
          bedNum = reservation._beds[0];
        } else {
          bedNum = (reservation.unusedZone)?1:0;
        }
      } else {
        bedNum = nbed;
      }

      // Search Initial Cell
      if (reservation.startDate.clone().local().isSameOrAfter(this.options.startDate, 'd')) {
        reservation._drawModes[0] = 'hard-start';
        limits.left = this.getCell(reservation.startDate.clone().local(),
                                   reservation.room,
                                   bedNum);
      }
      else {
        reservation._drawModes[0] = 'soft-start';
        limits.left = this.getCell(this.options.startDate.clone().local(),
                                   reservation.room,
                                   bedNum);
      }

      // More Beds?
      var rpersons = (reservation.room.shared || this.options.divideRoomsByCapacity)?reservation.room.capacity:1;
      var reservPersons = reservation.getTotalPersons(false);
      if ((reservation.room.shared || this.options.divideRoomsByCapacity) && reservPersons > 1 && bedNum+reservPersons <= rpersons) {
        bedNum += reservPersons-1;
      }

      // Search End Cell
      if (reservation.endDate.clone().subtract(1, 'd').local().isSameOrBefore(this._endDate, 'd')) {
        reservation._drawModes[1] = 'hard-end';
        limits.right = this.getCell(reservation.endDate.clone().subtract(1, 'd').local(),
                                   reservation.room,
                                   bedNum);
      }
      else {
        reservation._drawModes[1] = 'soft-end';
        limits.right = this.getCell(this._endDate.clone().local(),
                                   reservation.room,
                                   bedNum);
      }

      // Exists other reservation in the same place?
      if (!notCheck && limits.isValid()) {
        var diff_date = this.getDateDiffDays(reservation.startDate, reservation.endDate);
        var numBeds = +limits.right.dataset.hcalBedNum - +limits.left.dataset.hcalBedNum;
        var ndate = reservation.startDate.clone().local();
        for (var i=0; i<diff_date; ++i) {
          var reservs = this.getReservationsByDay(ndate, true, true, reservation.room.id, +limits.left.dataset.hcalBedNum, reservation);
          if (reservs.length) {
            notFound = true;
            nbed = nbed?nbed+1:+limits.left.dataset.hcalBedNum+1;
            break;
          }
          ndate.add(1, 'd');
        }
      }
    } while (notFound && nbed < reservation.room.capacity);

    reservation._limits = limits;

    // Update Beds
    if (limits.isValid()) {
      var numBeds = (+limits.right.dataset.hcalBedNum)-(+limits.left.dataset.hcalBedNum);
      reservation._beds = [];
      for (var i=0; i<=numBeds; reservation._beds.push(+limits.left.dataset.hcalBedNum+i++));
    }
  },

  //==== CELLS
  getMainCell: function(/*MomentObject*/date, /*String*/type, /*String*/number) {
    return this.etable.querySelector('#'+this._sanitizeId(`${type}_${number}_${date.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
  },

  getCell: function(/*MomentObject*/date, /*HRoomObj*/room, /*Int*/bednum) {
    return this.etable.querySelector("td[data-hcal-date='"+date.format(HotelCalendar.DATE_FORMAT_SHORT_)+"'][data-hcal-room-obj-id='"+room.id+"'] table td[data-hcal-bed-num='"+bednum+"']");
  },

  getCells: function(/*HLimitObject*/limits) {
    var parentRow = this.$base.querySelector(`#${limits.left.dataset.hcalParentRow}`);
    var parentCell = this.$base.querySelector(`#${limits.left.dataset.hcalParentCell}`);
    if (!parentRow || !parentCell) {
      return [];
    }
    var room = this.getRoom(parentRow.dataset.hcalRoomObjId);
    var start_date = HotelCalendar.toMoment(this.etable.querySelector(`#${limits.left.dataset.hcalParentCell}`).dataset.hcalDate);
    var end_date = HotelCalendar.toMoment(this.etable.querySelector(`#${limits.right.dataset.hcalParentCell}`).dataset.hcalDate);
    var diff_date = this.getDateDiffDays(start_date, end_date);

    var cells = [];
    var numBeds = +limits.right.dataset.hcalBedNum-+limits.left.dataset.hcalBedNum;
    for (var nbed=0; nbed<=numBeds; nbed++) {
      var date = start_date.clone();
      var cell = this.getCell(date, room, +limits.left.dataset.hcalBedNum+nbed);
      if (cell) {
        cells.push(cell);
      }
      for (var i=0; i<diff_date; i++) {
        cell = this.getCell(
          date.add(1, 'd'),
          room,
          +limits.left.dataset.hcalBedNum+nbed);
        if (cell) {
          cells.push(cell);
        }
      }
    }

    return cells;
  },

  //==== ROOMS
  _filterRooms: function() {
    // Two-Step filter: Scrollbar mistake
    this.options.room_classes = [];
    this.options.room_types = [];
    // 1.1 Filter rooms
    for (var r of this.options.rooms) {
      r._active = this._in_domain(r, this._domains[HotelCalendar.DOMAIN.ROOMS]);
      if (r._active) {
        r._html.classList.remove('hcal-hidden');
        // 1.2 Filter room classes used in occupation rows
        if (this.options.room_classes.indexOf(r.type) === -1) {
            this.options.room_classes.push(r.type);
        }
        // 1.3 Filter room types used in pricelist rows
        if (this.options.room_types.indexOf(r._userData.room_type_id) === -1) {
            this.options.room_types.push(r._userData.room_type_id);
        }
      } else {
        r._html.classList.add('hcal-hidden');
      }
    }
    // Hide all the rows corresponding to occupation and prices
    $("[id^=ROW_DETAIL_FREE_TYPE]").addClass('hcal-hidden');
    $("[id^=ROW_DETAIL_PRICE_ROOM]").addClass('hcal-hidden');
    // TODO: update OCCUPATION

    this._calcViewHeight();

    // 2. Update Reservations
    _.defer(function(self){
      for (var r of self.options.rooms) {
        var isHidden = r._html.classList.contains('hcal-hidden');
        if (r.id in self._reservationsMap) {
          for (var reserv of self._reservationsMap[r.id]) {
            self._updateReservation(reserv, isHidden);
          }
        }
      }
      // 2.2 Update room classes
      for (var room_class of self.options.room_classes)
      {
          var tr_name = self._sanitizeId(`ROW_DETAIL_FREE_TYPE_${room_class}`);
          var x = _.findWhere(self.edtable.rows, {id: tr_name});
          x.classList.remove('hcal-hidden');
      }
      // 2.3 Update room types
      for (var room_type of self.options.room_types)
      {
          var tr_name = self._sanitizeId(`ROW_DETAIL_PRICE_ROOM_${self._pricelist_id}_${room_type}`);
          var x = _.findWhere(self.edtable.rows, {id: tr_name});
          x.classList.remove('hcal-hidden');
      }
    }, this);
    //_.defer(function(){ this._updateReservationOccupation() }.bind(this));
  },

  getDayRoomTypeReservations: function(/*String,MomentObject*/day, /*String*/room_type) {
    return _.filter(this.getReservationsByDay(day, true), function(item){ return item.room && item.room.type === room_type && !item.unusedZone; });
  },

  getRoomTypes: function() {
    return _.keys(this._roomsMap);
  },

  getRoom: function(/*String,Int*/id, /*Boolean?*/isExtra, /*Int?*/reservId) {
    if (isExtra) {
      return _.find(this.options.rooms, function(item){ return item.id === `${reservId}@${id}` && (item.overbooking || item.cancelled); });
    }
    return _.find(this.options.rooms, function(item){ return item.id == id; });
  },

  _insertRoomAt: function(/*HRoomObject*/roomI, /*HRoomObject*/newRoom, /*Boolean*/isAfter) {
    this.options.rooms.splice(_.indexOf(this.options.rooms, roomI)+(isAfter?1:0), 0, newRoom);
  },

  getRoomPrice: function(/*String,HRoom*/id, /*String,MomentObject*/day) {
    var day = HotelCalendar.toMoment(day);
    if (!day) {
      return 0.0;
    }

    var room = id;
    if (!(room instanceof HRoom)) {
      room = this.getRoom(id);
    }
    if (room.price[0] == 'fixed') {
      return room.price[1];
    } else if (room.price[0] == 'pricelist') {
      var pricelist = _.find(this._pricelist[this._pricelist_id], function(item){ return item.room == room.price[1]; });
      if (day.format(HotelCalendar.DATE_FORMAT_SHORT_) in pricelist['days']) {
          return pricelist['days'][day.format(HotelCalendar.DATE_FORMAT_SHORT_)];
      }
    }

    return 0.0;
  },

  // Extra Room (Overbooking, cancelled, ...)
  getExtraRooms: function(/*Int*/parentRoomId) {
    var $this = this;
    return _.filter(this.options.rooms, function(item) {
      return ((item.overbooking || item.cancelled) && +$this.parseExtraRoomId(item.id)[1] === +parentRoomId);
    });
  },

  removeExtraRoomRow: function(/*HReservationObject*/ex_reserv) {
    if (!ex_reserv.room.overbooking && !ex_reserv.room.cancelled) {
      console.warn(`[HotelCalendar][removeExtraRoomRow] Can't remove the row for room ${ex_reserv.room.id}`);
      return false;
    }

    var exRoomRow = this.getExtraRoomRow(ex_reserv);
    if (exRoomRow) {
      // Update Reservations Position
      var bounds = this.loopedOffsetOptimized(exRoomRow);
      var start_index = _.indexOf(this.options.rooms, ex_reserv.room) + 1;
      for (var i=start_index; i<this.options.rooms.length; i++) {
        var reservs = this.getReservationsByRoom(this.options.rooms[i], true);
        for (var reserv of reservs) {
          if (reserv && reserv._html) {
            var top = parseInt(reserv._html.style.top, 10);
            reserv._html.style.top = `${top - bounds.height}px`;
          }
        }
      }

      exRoomRow.parentNode.removeChild(exRoomRow);
      this.options.rooms = _.reject(this.options.rooms, {id: ex_reserv.room.id});
    }
  },

  getRealExtraRoomInfo: function(/*HRoomObject*/room) {
    // Obtain the original room row
    var cnumber = this.getExtraRoomRealNumber(room);
    var mainRoomRowId = this._sanitizeId(`ROW_${cnumber}_${room.type}`);
    var mainRoomRow = this.e.querySelector('#'+mainRoomRowId);
    if (!mainRoomRow) {
      return false;
    }

    return [this.getRoom(mainRoomRow.dataset.hcalRoomObjId), mainRoomRow];
  },

  getExtraRoomRealNumber: function(/*HRoomObject*/room) {
    var isf = room.number.search(this._extraRowIndicators[0]);
    var isfb = room.number.search(this._extraRowIndicators[1]);
    var cnumber = room.number;
    if (isf != -1 && isfb != -1) { cnumber = cnumber.substr(isf+3, isfb-(isf+3)); }
    return cnumber;
  },

  getExtraRoomRow: function(/*HReservationObject*/ex_reserv) {
    var cnumber = this.getExtraRoomRealNumber(ex_reserv.room);
    return this.e.querySelector(`#${this._sanitizeId(`ROW_${cnumber}_${ex_reserv.room.type}_EXTRA${ex_reserv.id}`)}`);
  },

  parseExtraRoomId: function(/*String*/id) {
    if (typeof id !== 'number') {
      return id.split('@');
    }
    return id;
  },

  createExtraRoom: function(/*HRoomObject*/mainRoom, /*Int*/reservId, /*Dict*/extraData) {
    var exr = this.getExtraRooms(mainRoom.id);
    var ex_room = mainRoom.clone();
    ex_room.id = `${reservId}@${mainRoom.id}`;
    ex_room.number = `${this._extraRowIndicators[0]}${mainRoom.number}${this._extraRowIndicators[1]}${exr.length}`;
    for (var key in extraData) {
      ex_room[key] = extraData[key];
    }
    this._insertRoomAt(mainRoom, ex_room, true);
    return ex_room;
  },

  createExtraRoomRow: function(/*HRoomObject*/ex_room) {
    var mainRoomInfo = this.getRealExtraRoomInfo(ex_room);
    var exRoomId = this.parseExtraRoomId(ex_room.id);
    if (!mainRoomInfo) {
      console.warn(`[HotelCalendar][createExtraRoomRow] Can't found room row: ${mainRoomRowId}`);
      return false;
    }
    var mainRoom = mainRoomInfo[0];
    var mainRoomRow = mainRoomInfo[1];

    var row = document.createElement("TR");
    row.setAttribute('id', this._sanitizeId(`ROW_${mainRoom.number}_${ex_room.type}_EXTRA${exRoomId[0]}`));
    row.classList.add('hcal-row-room-type-group-item');
    if (ex_room.overbooking) {
      row.classList.add('hcal-row-room-type-group-overbooking-item');
    } else if (ex_room.cancelled) {
      row.classList.add('hcal-row-room-type-group-cancelled-item');
    }
    row.dataset.hcalRoomObjId = ex_room.id;
    mainRoomRow.parentNode.insertBefore(row, mainRoomRow.nextSibling);

    var cell = row.insertCell();
    cell.textContent = ex_room.number;
    cell.classList.add('hcal-cell-room-type-group-item');
    cell.classList.add('btn-hcal');
    cell.classList.add('btn-hcal-3d');
    cell.setAttribute('colspan', '3');
    /*
    cell = row.insertCell();
    cell.textContent = ex_room.type;
    cell.classList.add('hcal-cell-room-type-group-item');
    cell.classList.add('btn-hcal');
    cell.classList.add('btn-hcal-flat');
   */
    var now = moment();
    for (var i=0; i<=this.options.days; i++) {
      var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
      var dd_local = dd.clone().local();
      cell = row.insertCell();
      cell.setAttribute('id', this._sanitizeId(`${ex_room.type}_${ex_room.number}_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
      cell.classList.add('hcal-cell-room-type-group-item-day');
      cell.dataset.hcalParentRow = row.getAttribute('id');
      cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
      cell.dataset.hcalRoomObjId = ex_room.id;
      // Generate Interactive Table
      cell.appendChild(this._generateTableDay(cell, ex_room));
      //cell.innerHTML = dd.format("DD");
      var day = +dd_local.format("D");
      if (day == 1) {
        cell.classList.add('hcal-cell-start-month');
      }
      if (dd_local.isSame(now, 'day')) {
        cell.classList.add('hcal-cell-current-day');
      }  else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
        cell.classList.add('hcal-cell-end-week');
      }
    }

    // Update Reservations Position
    var bounds = this.loopedOffsetOptimized(row);
    var cheight = bounds.height;
    var start_index = _.indexOf(this.options.rooms, ex_room) + 1;
    for (var i=start_index; i<this.options.rooms.length; ++i) {
      var reservs = this.getReservationsByRoom(this.options.rooms[i], true);
      for (var reserv of reservs) {
        if (reserv && reserv._html) {
          var top = parseInt(reserv._html.style.top, 10);
          reserv._html.style.top = (cheight === 0)?'0':`${top + cheight}px`;
        }
      }
    }

    return row;
  },

  //==== RESTRICTIONS
  setRestrictions: function(/*Object*/restrictions) {
    this._restrictions = restrictions;
    this._updateRestrictions();
  },

  _updateRestrictions: function() {
    // Clean
    var restDays = this.e.querySelectorAll('.hcal-restriction-room-day');
	  for (var rd of restDays) {
      rd.title = '';
      rd.classList.remove('hcal-restriction-room-day');
	  }

    if (this._restrictions) {
      // Rooms Restrictions
      for (var room of this.options.rooms) {
        var date = this.options.startDate.clone().startOf('day');
        for (var i=0; i<=this.options.days; ++i) {
          var dd = date.add(1, 'd');
          var date_str = dd.format(HotelCalendar.DATE_FORMAT_SHORT_);
          if (date_str in this._restrictions[room.price[1]]) {
            var restr = this._restrictions[room.price[1]][date_str];
            if (restr) {
              var cell = this.getMainCell(dd, room.type, room.number);
              if (cell) {
                if (restr[0] || restr[1] || restr[2] || restr[3] || restr[4] || restr[5] || restr[6]) {
                  cell.classList.add('hcal-restriction-room-day');
                  var humantext = "Restrictions:\n";
                  if (restr[0] > 0)
                    humantext += `Min. Stay: ${restr[0]}\n`;
                  if (restr[1] > 0)
                    humantext += `Min. Stay Arrival: ${restr[1]}\n`;
                  if (restr[2] > 0)
                    humantext += `Max. Stay: ${restr[2]}\n`;
                  if (restr[3] > 0)
                    humantext += `Max. Stay Arrival: ${restr[3]}\n`;
                  if (restr[4])
                    humantext += `Closed: ${restr[4]}\n`;
                  if (restr[5])
                    humantext += `Closed Arrival: ${restr[5]}\n`;
                  if (restr[6])
                    humantext += `Closed Departure: ${restr[6]}`;
                  cell.title = humantext;
                }
                else {
                  cell.classList.remove('hcal-restriction-room-day');
                  cell.title = '';
                }
              }
            }
          }
        }
      }
    }
  },

  //==== DETAIL CALCS
  calcDayRoomTypeReservations: function(/*String,MomentObject*/day, /*String*/room_type) {
    var day = HotelCalendar.toMoment(day);
    if (!day) { return false; }

    var num_rooms = this._roomCapacities[room_type];
    num_rooms -= _.reduce(this.getDayRoomTypeReservations(day, room_type), function(memo, r){ return memo + ((r.room && r.room.shared)?r.getTotalPersons(false):1); }, 0);
    return num_rooms;
  },

  calcDayRoomTotalReservations: function(/*String,MomentObject*/day) {
    var day = HotelCalendar.toMoment(day);
    if (!day) { return false; }

    var num_rooms = this._roomCapacityTotal;
    num_rooms -= _.reduce(this.getReservationsByDay(day, true), function(memo, r){ return memo + ((r.room && r.room.shared)?r.getTotalPersons(false):1); }, 0);
    return num_rooms;
  },


  /** PRIVATE MEMBERS **/
  //==== MAIN FUNCTIONS
  _reset_action_reservation: function() {
    if (this._lazyModeReservationsSelection) {
      clearTimeout(this._lazyModeReservationsSelection);
      this._lazyModeReservationsSelection = false;
    }

    this.reservationAction = {
      action: HotelCalendar.ACTION.NONE,
      reservation: null,
      oldReservationObj: null,
      newReservationObj: null,
      mousePos: false,
      inReservations: [],
      outReservations: [],
    };
  },

  get_normalized_rooms_: function() {
    var rooms = {};
    if (this.options.rooms) {
      var keys = Object.keys(this.options.rooms);

      for (var r of this.options.rooms) {
        rooms[r.number] = [r.type, r.capacity];
      }
    }
    return rooms;
  },

  //==== RENDER FUNCTIONS
  _create: function() {
    var $this = this;
  	while (this.e.hasChildNodes()) {
  		this.e.removeChild(this.e.lastChild);
  	}

    if (this._tableCreated) {
      console.warn("[Hotel Calendar][_create] Already created!");
      return false;
    }

    var scrollThrottle = _.throttle(this._updateOBIndicators.bind(this), 100);


    this.edivcontainer = document.createElement("div");
    this.edivcontainer.classList.add('hcalendar-container');

    // Reservations Table
    this.edivrh = document.createElement("div");
    this.edivrh.classList.add('table-reservations-header');
    this.edivcontainer.appendChild(this.edivrh);
    this.etableHeader = document.createElement("table");
    this.etableHeader.classList.add('hcal-table');
    this.etableHeader.classList.add('noselect');
    this.edivrh.appendChild(this.etableHeader);
    this.edivr = document.createElement("div");
    this.edivr.classList.add('table-reservations');
    this.edivcontainer.appendChild(this.edivr);
    this.etable = document.createElement("table");
    this.etable.classList.add('hcal-table');
    this.etable.classList.add('noselect');
    this.edivr.appendChild(this.etable);
    this.edivr.addEventListener("scroll", scrollThrottle, false);
    // Detail Calcs Table
    this.edivch = document.createElement("div");
    this.edivch.classList.add('table-calcs-header');
    this.edivcontainer.appendChild(this.edivch);
    this.edtableHeader = document.createElement("table");
    this.edtableHeader.classList.add('hcal-table');
    this.edtableHeader.classList.add('noselect');
    this.edivch.appendChild(this.edtableHeader);
    this.edivc = document.createElement("div");
    this.edivc.classList.add('table-calcs');
    this.edivcontainer.appendChild(this.edivc);
    this.edtable = document.createElement("table");
    this.edtable.classList.add('hcal-table');
    this.edtable.classList.add('noselect');
    this.edivc.appendChild(this.edtable);

    var observer = new MutationObserver(function(mutationsList){
      $this._updateOBIndicators();
    });
    observer.observe(this.edivr, { childList: true });

    this.e.appendChild(this.edivcontainer);

    this._updateView();
    //_.defer(function(self){ self._updateView(); }, this);
    this._tableCreated = true;

    return true;
  },

  _generateTableDay: function(/*HTMLObject*/parentCell, /*HRoomObject*/room) {
    var $this = this;
    var table = document.createElement("table");
    table.classList.add('hcal-table-day');
    table.classList.add('noselect');
    var row = false;
    var cell = false;
    var num = ((room.shared || this.options.divideRoomsByCapacity)?room.capacity:1);
    for (var i=0; i<num; i++) {
      row = table.insertRow();
      cell = row.insertCell();
      cell.dataset.hcalParentRow = parentCell.dataset.hcalParentRow;
      cell.dataset.hcalParentCell = parentCell.getAttribute('id');
      cell.dataset.hcalBedNum = i;
      cell.addEventListener('mouseenter', this._onCellMouseEnter.bind(this), false);
      cell.addEventListener('mousedown', this._onCellMouseDown.bind(this), false);
      cell.addEventListener('mouseup', this._onCellMouseUp.bind(this), false);
    }

    return table;
  },

  _createTableReservationDays: function() {
    var $this = this;
    this.etableHeader.innerHTML = "";
    this.etable.innerHTML = "";
    /** TABLE HEADER **/
    var thead = this.etableHeader.createTHead();
    var row = thead.insertRow();
    var row_init = row;
    // Current Date
    var cell = row.insertCell();
    cell.setAttribute('rowspan', 2);
    cell.setAttribute('colspan', 3);
    cell.classList.add('hcal-cell-pagination');

    var button = document.createElement('button');
    button.setAttribute('id', 'cal-pag-prev-plus');
    button.classList.add('btn');
    button.style.minHeight = 0;
    button.addEventListener('click', function(){
      this.setStartDate(this.options.startDate.clone().subtract(this.options.paginatorStepsMax-1, 'd'), undefined, true);
      this._dispatchEvent('hcalOnDateChanged', { 'date_begin': this.options.startDate.clone().add(1, 'd'), 'date_end': this._endDate.clone() });
    }.bind(this));
    var buttonIcon = document.createElement('i');
    buttonIcon.classList.add('fa', 'fa-2x', 'fa-angle-double-left');
    button.appendChild(buttonIcon);
    cell.appendChild(button);
    button = button.cloneNode(true);
    button.setAttribute('id', 'cal-pag-prev');
    button.firstElementChild.classList.remove('fa-angle-double-left');
    button.firstElementChild.classList.add('fa-angle-left');
    button.addEventListener('click', function(){
      this.setStartDate(this.options.startDate.subtract(this.options.paginatorStepsMin-1, 'd'), undefined, true);
      this._dispatchEvent('hcalOnDateChanged', { 'date_begin': this.options.startDate.clone().add(1, 'd'), 'date_end': this._endDate.clone() });
    }.bind(this));
    cell.appendChild(button);

    button = button.cloneNode(true);
    button.setAttribute('id', 'cal-pag-selector');
    button.firstElementChild.classList.remove('fa-angle-left');
    button.firstElementChild.classList.add('fa-calendar');
    if (this.options.startDate.isSame(moment().utc().subtract(1, 'd'), 'd')) {
      // TODO
    } else {
      button.addEventListener('click', function(){
        this.setStartDate(moment().utc(), undefined, true);
        this._dispatchEvent('hcalOnDateChanged', { 'date_begin': this.options.startDate.clone().add(1, 'd'), 'date_end': this._endDate.clone() });
      }.bind(this));
    }
    cell.appendChild(button);

    button = button.cloneNode(true);
    button.setAttribute('id', 'cal-pag-next');
    button.firstElementChild.classList.remove('fa-calendar');
    button.firstElementChild.classList.add('fa-angle-right');
    button.addEventListener('click', function(){
      this.setStartDate(this.options.startDate.add(this.options.paginatorStepsMin+1, 'd'), undefined, true);
      this._dispatchEvent('hcalOnDateChanged', { 'date_begin': this.options.startDate.clone().add(1, 'd'), 'date_end': this._endDate.clone() });
    }.bind(this));
    cell.appendChild(button);
    button = button.cloneNode(true);
    button.setAttribute('id', 'cal-pag-next-plus');
    button.firstElementChild.classList.remove('fa-angle-right');
    button.firstElementChild.classList.add('fa-angle-double-right');
    button.addEventListener('click', function(){
      this.setStartDate(this.options.startDate.add(this.options.paginatorStepsMax+1, 'd'), undefined, true);
      this._dispatchEvent('hcalOnDateChanged', { 'date_begin': this.options.startDate.clone().add(1, 'd'), 'date_end': this._endDate.clone() });
    }.bind(this));
    cell.appendChild(button);

    var edit = document.createElement('input');
    edit.style.width = "100%";
    edit.style.display = 'block';
    edit.setAttribute('id', 'cal-search-query');
    edit.setAttribute('placeholder', 'Search...');
    cell.appendChild(edit);

    edit.addEventListener('keypress', function(ev){
      if (ev.keyCode === 13) {
        var query = ev.target.value;
        this.setDomain(HotelCalendar.DOMAIN.RESERVATIONS, [
          ['title', 'ilike', query]
        ]);
      }
    }.bind(this), false);

    // Render Next Days
    row = thead.insertRow();
    var months = { };
    var cur_month = this.options.startDate.clone().local().format("MMMM");
    months[cur_month] = {};
    months[cur_month].year = this.options.startDate.clone().local().format("YYYY");
    months[cur_month].colspan = 0;
    var now = moment();
    for (var i=0; i<=this.options.days; i++) {
      var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
      var dd_local = dd.clone().local();
      cell = row.insertCell();
      cell.setAttribute('id', this._sanitizeId(`hday_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
      cell.classList.add('hcal-cell-header-day');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-3d');
      cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
      cell.innerHTML = `${dd_local.format('ddd')}<br/>${dd_local.format('D')}`;
      cell.setAttribute('title', dd_local.format('dddd'))
      var day = +dd_local.format('D');
      if (day == 1) {
        cell.classList.add('hcal-cell-start-month');
        cur_month = dd_local.format('MMMM');
        months[cur_month] = {};
        months[cur_month].year = dd_local.format('YYYY');
        months[cur_month].colspan = 0;
      }
      if (dd_local.isSame(now, 'day')) {
        cell.classList.add('hcal-cell-current-day');
      } else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
        cell.classList.add('hcal-cell-end-week');
      }
      ++months[cur_month].colspan;
    }
    // Render Months
    var month_keys = Object.keys(months);
    for (var m of month_keys) {
      var cell_month = row_init.insertCell();
      cell_month.setAttribute('colspan', months[m].colspan);
      cell_month.innerText = m+' '+months[m].year;
      cell_month.classList.add('hcal-cell-month');
      cell_month.classList.add('btn-hcal');
      cell_month.classList.add('btn-hcal-3d');
    }

    /** ROOM LINES **/
    var tbody = document.createElement("tbody");
    this.etable.appendChild(tbody);
    for (var itemRoom of this.options.rooms) {
      // Room Number
      row = tbody.insertRow();
      row.dataset.hcalRoomObjId = itemRoom.id;
      row.classList.add('hcal-row-room-type-group-item');
      if ((this.options.showOverbookings && itemRoom.overbooking) || (this.options.showCancelled && itemRoom.cancelled)) {
        var reservId = this.parseExtraRoomId(itemRoom.id)[0];
        var cnumber = this.getExtraRoomRealNumber(itemRoom);
        row.setAttribute('id', this._sanitizeId(`ROW_${cnumber}_${itemRoom.type}_EXTRA${reservId}`));
        row.classList.add('hcal-row-room-type-group-overbooking-item');
      } else {
        row.setAttribute('id', $this._sanitizeId(`ROW_${itemRoom.number}_${itemRoom.type}`));
      }
      cell = row.insertCell();
      cell.textContent = itemRoom.number;
      cell.classList.add('hcal-cell-room-type-group-item');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-left');
      cell.setAttribute('colspan', '3');
      /*
      cell = row.insertCell();
      cell.textContent = itemRoom.type;
      cell.classList.add('hcal-cell-room-type-group-item');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-flat');
      */
      for (var i=0; i<=$this.options.days; i++) {
        var dd = $this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
        var dd_local = dd.clone().local();
        cell = row.insertCell();
        cell.setAttribute('id', $this._sanitizeId(`${itemRoom.type}_${itemRoom.number}_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
        cell.classList.add('hcal-cell-room-type-group-item-day');
        cell.dataset.hcalParentRow = row.getAttribute('id');
        cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
        cell.dataset.hcalRoomObjId = itemRoom.id;
        // Generate Interactive Table
        cell.appendChild($this._generateTableDay(cell, itemRoom));
        //cell.innerHTML = dd.format("DD");
        var day = +dd_local.format("D");
        if (day == 1) {
          cell.classList.add('hcal-cell-start-month');
        }
        if (dd_local.isSame(now, 'day')) {
          cell.classList.add('hcal-cell-current-day');
        }  else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
          cell.classList.add('hcal-cell-end-week');
        }
      }

      itemRoom._html = row;
    }

    this._filterRooms();
    this._calcViewHeight();
  },

  _calcViewHeight: function() {
    if (this.options.showNumRooms > 0) {
      var rows = this.edivr.querySelectorAll('tr.hcal-row-room-type-group-item');
      var cheight = 0.0;
      for (var i=0; i<this.options.showNumRooms && i<rows.length; ++i)
      {
        cheight += rows[i].offsetHeight;
      }
      this.edivr.style.height = `${cheight}px`;
      this.edivr.style.maxHeight = 'initial';
    }
  },

  _createTableDetailDays: function() {
    var $this = this;
    this.edtableHeader.innerHTML = "";
    this.edtable.innerHTML = "";
    /** DETAIL DAYS HEADER **/
    var now = moment();
    var thead = this.edtableHeader.createTHead();
    var row = thead.insertRow();
    var cell = row.insertCell();
    cell.setAttribute('colspan', 3);
    this.btnSaveChanges = document.createElement('button');
    if (this.options.showPricelist) {
      this.btnSaveChanges.classList.add('btn', 'col-xs-12', 'col-lg-12');
      this.btnSaveChanges.setAttribute('id', 'btn_save_changes');
      this.btnSaveChanges.style.height = '45px';
      this.btnSaveChanges.setAttribute('title', this._t('Save Changes'));
      this.btnSaveChanges.innerHTML = "<i class='fa fa-save fa-2x'> </i>";
      this.btnSaveChanges.addEventListener('click', function(ev){
        if (this.classList.contains('need-save')) {
          $this._dispatchEvent('hcalOnSavePricelist', {
            pricelist: $this.getPricelist(),
            pricelist_id: $this._pricelist_id,
          });
        }
      });
      // Initialize Save Button state to disable
      this.btnSaveChanges.disabled = true;
      cell.appendChild(this.btnSaveChanges);
    }
    //cell.setAttribute('class', 'col-xs-1 col-lg-1');
    for (var i=0; i<=this.options.days; i++) {
      var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
      var dd_local = dd.clone().local();
      cell = row.insertCell();
      cell.setAttribute('id', this._sanitizeId(`hday_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
      cell.classList.add('hcal-cell-header-day');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-3d');
      cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
      cell.innerHTML = `${dd_local.format('ddd')}<br/>${dd_local.format('D')}`;
      cell.setAttribute('title', dd_local.format("dddd"))
      var day = +dd_local.format("D");
      if (day == 1) {
        cell.classList.add('hcal-cell-start-month');
      }
      if (dd_local.isSame(now, 'day')) {
        cell.classList.add('hcal-cell-current-day');
      } else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
        cell.classList.add('hcal-cell-end-week');
      }
    }

    /** DETAIL LINES **/
    var tbody = document.createElement("tbody");
    this.edtable.appendChild(tbody);
    if (this.options.showAvailability) {
      // Rooms Free Types
      if (this.options.rooms) {
        var room_types = this.getRoomTypes();
        for (var rt of room_types) {
          if (rt || room_types.length > 1) {
            row = tbody.insertRow();
            row.setAttribute('id', this._sanitizeId(`ROW_DETAIL_FREE_TYPE_${rt}`));
            row.dataset.hcalRoomType = rt;
            row.classList.add('hcal-row-detail-room-free-type-group-item');
            cell = row.insertCell();
            cell.textContent = rt;
            cell.classList.add('hcal-cell-detail-room-free-type-group-item');
            cell.classList.add('btn-hcal');
            cell.classList.add('btn-hcal-left');
            cell.setAttribute("colspan", "3");
            for (var i=0; i<=this.options.days; i++) {
              var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
              var dd_local = dd.clone().local();
              cell = row.insertCell();
              cell.setAttribute('id', this._sanitizeId(`CELL_FREE_${rt}_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
              cell.classList.add('hcal-cell-detail-room-free-type-group-item-day');
              cell.dataset.hcalParentRow = row.getAttribute('id');
              cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
              cell.textContent = '0';
              var day = +dd_local.format("D");
              if (day == 1) {
                cell.classList.add('hcal-cell-start-month');
              }
              if (dd_local.isSame(now, 'day')) {
                cell.classList.add('hcal-cell-current-day');
              } else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
                cell.classList.add('hcal-cell-end-week');
              }
            }
          }
        }
      }
      // Total Free
      row = tbody.insertRow();
      row.setAttribute('id', "ROW_DETAIL_TOTAL_FREE");
      row.classList.add('hcal-row-detail-room-free-total-group-item');
      cell = row.insertCell();
      cell.textContent = 'FREE TOTAL';
      cell.classList.add('hcal-cell-detail-room-free-total-group-item');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-left');
      cell.setAttribute("colspan", "3");
      for (var i=0; i<=this.options.days; i++) {
        var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
        var dd_local = dd.clone().local();
        cell = row.insertCell();
        cell.setAttribute('id', this._sanitizeId(`CELL_DETAIL_TOTAL_FREE_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
        cell.classList.add('hcal-cell-detail-room-free-total-group-item-day');
        cell.dataset.hcalParentRow = row.getAttribute('id');
        cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
        cell.textContent = '0';
        var day = +dd_local.format("D");
        if (day == 1) {
          cell.classList.add('hcal-cell-start-month');
        }
        if (dd_local.isSame(now, 'day')) {
          cell.classList.add('hcal-cell-current-day');
        }  else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
          cell.classList.add('hcal-cell-end-week');
        }
      }
      // Percentage Occupied
      row = tbody.insertRow();
      row.setAttribute('id', "ROW_DETAIL_PERC_OCCUP");
      row.classList.add('hcal-row-detail-room-perc-occup-group-item');
      cell = row.insertCell();
      cell.textContent = '% OCCUP.';
      cell.classList.add('hcal-cell-detail-room-perc-occup-group-item');
      cell.classList.add('btn-hcal');
      cell.classList.add('btn-hcal-left');
      cell.setAttribute("colspan", "3");
      for (var i=0; i<=this.options.days; i++) {
        var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
        var dd_local = dd.clone().local();
        cell = row.insertCell();
        cell.setAttribute('id', this._sanitizeId(`CELL_DETAIL_PERC_OCCUP_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
        cell.classList.add('hcal-cell-detail-room-perc-occup-group-item-day');
        cell.dataset.hcalParentRow = row.getAttribute('id');
        cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
        cell.textContent = '0';
        var day = +dd_local.format("D");
        if (day == 1) {
          cell.classList.add('hcal-cell-start-month');
        }
        if (dd_local.isSame(now, 'day')) {
          cell.classList.add('hcal-cell-current-day');
        }  else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
          cell.classList.add('hcal-cell-end-week');
        }
      }
    }
    // Rooms Pricelist
    this._pricelist_id = _.keys(this._pricelist)[0];
    if (this.options.showPricelist && this._pricelist) {
      //var pricelists_keys = _.keys(this._pricelist)
      //for (var key of pricelists_keys) {
      var key = this._pricelist_id;
      var pricelist = this._pricelist[key];
      for (var listitem of pricelist) {
        row = tbody.insertRow();
        row.setAttribute('id', this._sanitizeId(`ROW_DETAIL_PRICE_ROOM_${key}_${listitem.room}`));
        row.dataset.hcalPricelist = key;
        row.dataset.hcalRoomTypeId = listitem.room
        row.classList.add('hcal-row-detail-room-price-group-item');
        cell = row.insertCell();
        var span = document.createElement('span');
        cell.title = cell.textContent = listitem.title + ' ' + this.options.currencySymbol;
        cell.classList.add('hcal-cell-detail-room-group-item', 'btn-hcal', 'btn-hcal-left');
        cell.dataset.currencySymbol = this.options.currencySymbol;
        cell.setAttribute("colspan", "3");
        for (var i=0; i<=$this.options.days; i++) {
      	var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
          var dd_local = dd.clone().local();
          cell = row.insertCell();
          cell.setAttribute('id', this._sanitizeId(`CELL_PRICE_${key}_${listitem.room}_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
          cell.classList.add('hcal-cell-detail-room-price-group-item-day');
          cell.dataset.hcalParentRow = row.getAttribute('id');
          cell.dataset.hcalDate = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
          var day = +dd_local.format("D");
          if (day == 1) {
            cell.classList.add('hcal-cell-start-month');
          }
          if (dd_local.isSame(now, 'day')) {
            cell.classList.add('hcal-cell-current-day');
          } else if (dd_local.format('e') >= this.options.endOfWeek-this.options.endOfWeekOffset && dd_local.format('e') <= this.options.endOfWeek) {
            cell.classList.add('hcal-cell-end-week');
          }

          var input = document.createElement('input');
          input.setAttribute('id', this._sanitizeId(`INPUT_PRICE_${key}_${listitem.room}_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`));
          input.setAttribute('type', 'edit');
          input.setAttribute('title', 'Price');
          input.setAttribute('name', 'room_type_price_day');
          input.dataset.hcalParentCell = cell.getAttribute('id');
          var dd_fmrt = dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_);
          input.dataset.orgValue = input.value = _.has(listitem['days'], dd_fmrt)?Number(listitem['days'][dd_fmrt]).toLocaleString():'...';
          input.addEventListener('change', function(ev){ $this._onInputChange(ev, this); }, false);
          cell.appendChild(input);
        }
      }
      //}
    }
  },

  //==== UPDATE FUNCTIONS
  _updateView: function(/*Bool*/notData, /*function*/callback) {
    this._createTableReservationDays();
    if (typeof callback !== 'undefined') {
      callback();
    }
    this._updateCellSelection();
    this._createTableDetailDays();

    _.defer(function(self){
      self._updateOffsets();
      self._updateReservations(true);
      if (!notData) {
        _.defer(function(self){
          self._updateRestrictions();
          self._updatePriceList();
          self._updateReservationOccupation();
        }, self);
      }
    }, this);
    // if (!notData) {
    //   _.defer(function(self){
    //     self._createTableDetailDays();
    //     self._updateRestrictions();
    //     self._updatePriceList();
    //     self._updateReservationOccupation();
    //   }, this);
    // }
  },

  _updateOBIndicators: function() {
    var mainBounds = this._edivrOffset;
    for (var reserv of this._reservations) {
      if (reserv.overbooking && reserv._html) {
        var eOffset = this._eOffset;
        var bounds = this.loopedOffsetOptimized(reserv._html);
        if (bounds.top > mainBounds.height) {
          var warnDiv = this.e.querySelector(`div.hcal-warn-ob-indicator[data-hcal-reservation-obj-id='${reserv.id}']`);
          if (!warnDiv) {
            var warnDiv = document.createElement("DIV");
            warnDiv.innerHTML = "<i class='fa fa-warning'></i>";
            warnDiv.classList.add('hcal-warn-ob-indicator');
            warnDiv.style.borderTopLeftRadius = warnDiv.style.borderTopRightRadius = "50px";
            warnDiv.dataset.hcalReservationObjId = reserv.id;
            this.edivcontainer.appendChild(warnDiv);
            var warnComputedStyle = window.getComputedStyle(warnDiv, null);
            warnDiv.style.top = `${mainBounds.height - eOffset.top - parseInt(warnComputedStyle.getPropertyValue("height"), 10)}px`;
            warnDiv.style.left = `${(bounds.left + (bounds.right - bounds.left)/2.0 - parseInt(warnComputedStyle.getPropertyValue("width"), 10)/2.0) - mainBounds.left}px`;
          }
        } else if (bounds.height < mainBounds.top) {
          var warnDiv = this.e.querySelector(`div.hcal-warn-ob-indicator[data-hcal-reservation-obj-id='${reserv.id}']`);
          if (!warnDiv) {
            var warnDiv = document.createElement("DIV");
            warnDiv.innerHTML = "<i class='fa fa-warning'></i>";
            warnDiv.classList.add('hcal-warn-ob-indicator');
            warnDiv.style.borderBottomLeftRadius = warnDiv.style.borderBottomRightRadius = "50px";
            warnDiv.style.top = `${mainBounds.top - eOffset.top}px`;
            warnDiv.dataset.hcalReservationObjId = reserv.id;
            this.edivcontainer.appendChild(warnDiv);
            var warnComputedStyle = window.getComputedStyle(warnDiv, null);
            warnDiv.style.left = `${(bounds.left + (bounds.right - bounds.left)/2.0 - parseInt(warnComputedStyle.getPropertyValue("width"), 10)/2.0) - mainBounds.left}px`;
          }
        } else {
          var warnDiv = this.e.querySelector(`div.hcal-warn-ob-indicator[data-hcal-reservation-obj-id='${reserv.id}']`);
          if (warnDiv) {
            warnDiv.parentNode.removeChild(warnDiv);
          }
        }
      }
    }
  },

  _updateHighlightUnifyReservations: function() {
    var $this = this;
    if (!this.reservationAction.toUnify || this.reservationAction.toUnify.length === 0) {
      var elms = this.e.querySelectorAll("div.hcal-reservation-invalid-unify");
      for (var elm of elms) { elm.classList.remove('hcal-reservation-invalid-unify'); }
      elms = this.e.querySelectorAll("div.hcal-reservation-unify-selected");
      for (var elm of elms) { elm.classList.remove('hcal-reservation-unify-selected'); }
    }
    else {
      var dateLimits = this.getDateLimits(this.reservationAction.toUnify, false);
      var refUnifyReservation = this.reservationAction.toUnify[0];
      var uniRoom = refUnifyReservation?refUnifyReservation.room.id:false;
      for (var nreserv of this._reservations) {
        if (nreserv.unusedZone || nreserv._html.classList.contains('hcal-reservation-unify-selected')) {
          continue;
        }

        // Invalid?
        if (nreserv.room.id !== uniRoom || (!nreserv.startDate.isSame(dateLimits[1], 'day') && !nreserv.endDate.isSame(dateLimits[0], 'day')) ||
            (nreserv.id !== refUnifyReservation.id && nreserv.getUserData('parent_reservation') !== refUnifyReservation.id))
        {
          nreserv._html.classList.add('hcal-reservation-invalid-unify');
        }
        else {
          nreserv._html.classList.remove('hcal-reservation-invalid-unify');
        }
      }
    }
  },

  _updateHighlightSwapReservations: function() {
    var $this = this;
    if (this.reservationAction.inReservations.length === 0 && this.reservationAction.outReservations.length === 0) {
      var elms = this.e.querySelectorAll("div.hcal-reservation-invalid-swap");
      for (var elm of elms) { elm.classList.remove('hcal-reservation-invalid-swap'); }
      elms = this.e.querySelectorAll("div.hcal-reservation-swap-in-selected");
      for (var elm of elms) { elm.classList.remove('hcal-reservation-swap-in-selected'); }
      elms = this.e.querySelectorAll("div.hcal-reservation-swap-out-selected");
      for (var elm of elms) { elm.classList.remove('hcal-reservation-swap-out-selected'); }
    }
    else {
      var dateLimits = this.getDateLimits(this.reservationAction.inReservations, true);
      var refInReservation = this.reservationAction.inReservations[0];
      var refOutReservation = this.reservationAction.outReservations[0];
      var inCapacity = refInReservation?refInReservation.room.capacity:false;
      var outCapacity = refOutReservation?refOutReservation.room.capacity:false;
      var realDateLimits = this.getFreeDatesByRoom(dateLimits[0], dateLimits[1], refInReservation?refInReservation.room.id:refOutReservation.room.id);
      for (var nreserv of this._reservations) {
        if (nreserv.unusedZone || nreserv._html.classList.contains('hcal-reservation-swap-in-selected') || nreserv._html.classList.contains('hcal-reservation-swap-out-selected')) {
          continue;
        }

        // Invalid capacity
        var totalReservPerson = nreserv.getTotalPersons(false);
        if (totalReservPerson > inCapacity || (outCapacity && totalReservPerson > outCapacity) || nreserv.room.capacity < refInReservation.getTotalPersons(false))
        {
          nreserv._html.classList.add('hcal-reservation-invalid-swap');
        }
        else if (this._modeSwap === HotelCalendar.MODE.SWAP_FROM && this.reservationAction.inReservations.length !== 0 && refInReservation.room.id !== nreserv.room.id) {
          if (!_.find(this.reservationAction.outReservations, {'id': nreserv.linkedId})) {
            nreserv._html.classList.add('hcal-reservation-invalid-swap');
          }
        } else if (this._modeSwap === HotelCalendar.MODE.SWAP_TO && this.reservationAction.outReservations.length !== 0 && refOutReservation.room.id !== nreserv.room.id) {
          if (!_.find(this.reservationAction.inReservations, {'id': nreserv.linkedId})) {
            nreserv._html.classList.add('hcal-reservation-invalid-swap');
          }
        }
        // Invalid reservations out of dates
        else if (nreserv.startDate.isBefore(realDateLimits[0], 'day') || nreserv.endDate.clone().subtract('1', 'd').isAfter(realDateLimits[1], 'day')) {
          if (nreserv.room.id !== refInReservation.room.id) {
            nreserv._html.classList.add('hcal-reservation-invalid-swap');
          }
        }
        else {
          nreserv._html.classList.remove('hcal-reservation-invalid-swap');
        }
      }
    }
  },

  _updateHighlightInvalidZones: function(/*HReservation*/reserv) {
    if (typeof reserv === 'undefined') {
      var elms = this.etable.querySelectorAll("td[data-hcal-date] table td");
      for (var tdCell of elms) {
        tdCell.classList.remove('hcal-cell-invalid');
      }
      return;
    }

    if (reserv.readOnly) {
      var elms = this.etable.querySelectorAll("td[data-hcal-date] table td");
      for (var tdCell of elms) {
        tdCell.classList.add('hcal-cell-invalid');
      }
    } else if (reserv.fixDays) {
      var limitLeftDate = this.etable.querySelector(`#${reserv._limits.left.dataset.hcalParentCell}`).dataset.hcalDate;
      var limitRightDate = this.etable.querySelector(`#${reserv._limits.right.dataset.hcalParentCell}`).dataset.hcalDate;
      var limitLeftDateMoment = HotelCalendar.toMoment(limitLeftDate);
      var limitRightDateMoment = HotelCalendar.toMoment(limitRightDate);
      var diff_date = this.getDateDiffDays(limitLeftDateMoment, limitRightDateMoment);
      var date = limitLeftDateMoment.clone().startOf('day');
      var selector = [];
      for (var i=0; i<=diff_date; i++) {
        selector.push("not([data-hcal-date='"+date.format(HotelCalendar.DATE_FORMAT_SHORT_)+"'])");
        date.add(1, 'd');
      }
      if (selector.length) {
        var elms = this.etable.querySelectorAll(`td:${selector.join(':')}`+ ' table td');
        for (var tdCell of elms) {
          tdCell.classList.add('hcal-cell-invalid');
        }
      }
    } else if (reserv.fixRooms) {
      var parentCell = this.etable.querySelector(`#${reserv._limits.left.dataset.hcalParentCell}`);
      var parent_row = parentCell.dataset.hcalParentRow;
      var elms = this.etable.querySelectorAll("td:not([data-hcal-parent-row='"+parent_row+"']) table td");
      for (var tdCell of elms) {
        tdCell.classList.add('hcal-cell-invalid');
      }
    } else {
      var limitLeftDate = this.etable.querySelector(`#${reserv._limits.left.dataset.hcalParentCell}`).dataset.hcalDate;
      var limitRightDate = this.etable.querySelector(`#${reserv._limits.right.dataset.hcalParentCell}`).dataset.hcalDate;
      var limitLeftDateMoment = HotelCalendar.toMoment(limitLeftDate);
      var limitRightDateMoment = HotelCalendar.toMoment(limitRightDate);
      var diff_date = this.getDateDiffDays(limitLeftDateMoment, limitRightDateMoment)+1;
      if (reserv._drawModes[1] === 'hard-end') { --diff_date; }
      var date = limitLeftDateMoment.clone().startOf('day');
      var selector = [];
      for (var i=0; i<=diff_date; i++) {
        selector.push("td[data-hcal-date='"+date.format(HotelCalendar.DATE_FORMAT_SHORT_)+"'] table td");
        date.add(1, 'd');
      }
      if (selector.length) {
        var elms = this.etable.querySelectorAll(`${selector.join(', ')}`);
        for (var tdCell of elms) {
          tdCell.classList.add('hcal-cell-highlight');
        }
      }
    }
  },

  _updateScroll: function(/*HTMLObject*/reservationDiv) {
    var reservBounds = this.loopedOffsetOptimized(reservationDiv);
    var mainBounds = this._edivrOffset;
    var eOffset = this._eOffset;
    var bottom = mainBounds.height - eOffset.top;
    var top = mainBounds.top + eOffset.top;
    var offset = 10.0;
    var scrollDisp = 10.0;
    if (reservBounds.height >= bottom-offset) {
      this.edivr.scrollBy(0, scrollDisp);
    }
    else if (reservBounds.top <= top+offset) {
      this.edivr.scrollBy(0, -scrollDisp);
    }
  },

  //==== SELECTION
  _updateCellSelection: function() {
      // Clear all
      var highlighted_td = this.etable.querySelectorAll('td.hcal-cell-highlight');
      for (var td of highlighted_td) {
        td.classList.remove('hcal-cell-highlight');
        td.textContent = '';
      }

      // Highlight Selected
      if (this._cellSelection.current) {
        this._cellSelection.current.classList.add('hcal-cell-highlight');
      }
      // Highlight Range Cells
      var cells = false;
      var total_price = 0.0;
      var limits = new HLimit(this._cellSelection.start,
                              this._cellSelection.end?this._cellSelection.end:this._cellSelection.current);
      if (limits.isValid()) {
        // Normalize
        // TODO: Multi-Directional Selection. Now only support normal or inverse.
        var limitLeftDate = HotelCalendar.toMoment(this.etable.querySelector(`#${limits.left.dataset.hcalParentCell}`).dataset.hcalDate);
        var limitRightDate = HotelCalendar.toMoment(this.etable.querySelector(`#${limits.right.dataset.hcalParentCell}`).dataset.hcalDate);
        if (limitLeftDate.isAfter(limitRightDate)) {
          limits.swap();
        }
        cells = this.getCells(limits);
        for (var c of cells) {
          var parentRow = this.$base.querySelector(`#${c.dataset.hcalParentRow}`);
          var room = this.getRoom(parentRow.dataset.hcalRoomObjId);
          if (room.overbooking || room.cancelled) {
            continue;
          }
          c.classList.add('hcal-cell-highlight');
          if (this._pricelist) {
            // FIXME: Normalize data calendar (gmt) vs extra info (utc)
            var date_cell = HotelCalendar.toMoment(this.etable.querySelector(`#${c.dataset.hcalParentCell}`).dataset.hcalDate);
            var room_price = this.getRoomPrice(parentRow.dataset.hcalRoomObjId, date_cell);
            c.textContent = room_price + ' ' + this.options.currencySymbol;
            if (!room.shared && c.dataset.hcalBedNum > limits.left.dataset.hcalBedNum) {
              c.style.color = 'lightgray';
            }
            else {
              c.style.color = 'black';
              total_price += room_price;
            }
          }
        }
      }

      this._dispatchEvent(
        'hcalOnUpdateSelection',
          {
            'limits': limits,
            'cells': cells,
            'old_cells': highlighted_td,
            'totalPrice': total_price
          });
  },

  _resetCellSelection: function() {
    this._cellSelection = { current: false, end: false, start: false };
  },

  //==== RESERVATIONS
  _updateDivReservation: function(/*HReservationObject*/reserv, /*Bool?*/noRefresh) {
    if (!reserv._limits.isValid() || !reserv._html) {
      return;
    }

    if (reserv.readOnly) {
      reserv._html.classList.add('hcal-reservation-readonly');
    } else {
      reserv._html.classList.remove('hcal-reservation-readonly');
    }

    if (reserv.room._active) {
      reserv._html.classList.remove('hcal-hidden');
    } else {
      reserv._html.classList.add('hcal-hidden');
    }

    if (reserv._active) {
      reserv._html.classList.remove('hcal-reservation-unselect');
    } else {
      reserv._html.classList.add('hcal-reservation-unselect');
    }

    if (!noRefresh) {
      var boundsInit = this.loopedOffsetOptimized(reserv._limits.left);
      var boundsEnd = this.loopedOffsetOptimized(reserv._limits.right);
      var divHeight = (boundsEnd.top+boundsEnd.height)-boundsInit.top-4;
      var has_changed = false;

      var reservStyles = {
        backgroundColor: reserv.color,
        color: reserv.colorText,
        lineHeight: `${divHeight}px`,
        fontSize: '12px',
        top: `${boundsInit.top-this._etableOffset.top+2}px`,
        left: `${boundsInit.left-this._etableOffset.left+2}px`,
        width: `${(boundsEnd.left-boundsInit.left)+boundsEnd.width-4}px`,
        height: `${divHeight}px`,
        borderLeftWidth: '',
        borderLeftStyle: '',
        borderRightWidth: '',
        borderRightStyle: '',
      };

      if (reserv._drawModes[0] === 'soft-start') {
        has_changed = true;
        reservStyles.borderLeftWidth = '3px';
        reservStyles.borderLeftStyle = 'double';
        reservStyles.left = `${boundsInit.left-this._etableOffset.left}px`;
        reservStyles.width = `${(boundsEnd.left-boundsInit.left)+boundsEnd.width-2}px`;
      } else if (reserv.splitted && reserv.startDate.isSame(reserv.getUserData('realDates')[0], 'day')) {
        has_changed = true;
        reservStyles.borderLeftWidth = '0';
        reservStyles.width = `${(boundsEnd.left-boundsInit.left)+boundsEnd.width-2}px`;
      }

      if (reserv._drawModes[1] === 'soft-end') {
        has_changed = true;
        reservStyles.borderRightWidth = '3px';
        reservStyles.borderRightStyle = 'double';
        reservStyles.width = `${(boundsEnd.left-boundsInit.left)+boundsEnd.width-2}px`;
      } else if (reserv.splitted && reserv.endDate.isSame(reserv.getUserData('realDates')[1], 'day')) {
        has_changed = true;
        reservStyles.borderRightWidth = '0';
        reservStyles.left = `${boundsInit.left-this._etableOffset.left-1}px`;
        reservStyles.width = `${(boundsEnd.left-boundsInit.left)+boundsEnd.width-1}px`;
      }

      if (reserv.splitted) {
        reserv._html.classList.add('hcal-reservation-splitted');
        // 1. Use reservation ID as seed
        // 2. Use sinusiudal function
        // 3. Only use positive values (This decrease longitude)
        // 4. Use the first 5 decimals to make the integer value
        // 5. Get integer value (Bitwise tilde method)
        // TODO: Improve pseudo-random number generator
        var magicNumber = ~~(Math.abs(Math.sin((reserv.getUserData('parent_reservation') || reserv.id))) * 100000);
        var bbColor = this._intToRgb(magicNumber);
        reservStyles.borderColor = `rgb(${bbColor[0]},${bbColor[1]},${bbColor[2]})`;

        if (!has_changed) {
          reservStyles.left = `${boundsInit.left-this._etableOffset.left-1}px`;
          reservStyles.width = `${(boundsEnd.left-boundsInit.left)+boundsEnd.width+2}px`;
        }
      } else {
        reserv._html.classList.remove('hcal-reservation-splitted');
      }

      Object.assign(reserv._html.style, reservStyles);
    }
  },

  swapReservations: function(/*List HReservationObject*/fromReservations, /*List HReservationObject*/toReservations) {
    if (fromReservations.length === 0 || toReservations.length === 0) {
      console.warn("[HotelCalendar][swapReservations] Invalid Swap Operation!");
      return false;
    }
    var fromDateLimits = this.getDateLimits(fromReservations, true);
    var fromRealDateLimits = this.getFreeDatesByRoom(fromDateLimits[0], fromDateLimits[1], fromReservations[0].room.id);
    var toDateLimits = this.getDateLimits(toReservations, true);
    var toRealDateLimits = this.getFreeDatesByRoom(toDateLimits[0], toDateLimits[1], toReservations[0].room.id);

    if (fromDateLimits[0].clone().local().isSameOrAfter(toRealDateLimits[0].clone().local(), 'd') && fromDateLimits[1].clone().local().isSameOrBefore(toRealDateLimits[1].clone().local(), 'd') &&
        toDateLimits[0].clone().local().isSameOrAfter(fromRealDateLimits[0].clone().local(), 'd') && toDateLimits[1].clone().local().isSameOrBefore(fromRealDateLimits[1].clone().local(), 'd'))
    {
      // Change some critical values
      var refFromReservs = fromReservations[0];
      var refToReservs = toReservations[0];
      var refFromRoom = refFromReservs.room;
      var refToRoom = refToReservs.room;
      var fromRoomRow = this.getExtraRoomRow(refFromReservs);
      var toRoomRow = this.getExtraRoomRow(refToReservs);
      var refFromRoomNewId = (refFromRoom.overbooking||refFromRoom.cancelled)?this.parseExtraRoomId(refFromRoom.id)[1]:refFromRoom.id;
      refFromRoomNewId = `${refToReservs.id}@${refFromRoomNewId}`;
      var refToRoomNewId = (refToRoom.overbooking||refToRoom.cancelled)?this.parseExtraRoomId(refToRoom.id)[1]:refToRoom.id;
      refToRoomNewId = `${refFromReservs.id}@${refToRoomNewId}`;

      if (refFromRoom.overbooking || refFromRoom.cancelled) {
        var cnumber = this.getExtraRoomRealNumber(refFromRoom);
        refFromRoom.id = refFromRoomNewId;
        var newRowId = `${this._sanitizeId(`ROW_${cnumber}_${refToRoom.type}_EXTRA${refToReservs.id}`)}`;
        var elms = fromRoomRow.querySelectorAll(`td[data-hcal-parent-row='${fromRoomRow.id}']`);
        for (var elm of elms) { elm.dataset.hcalParentRow = newRowId; }
        fromRoomRow.setAttribute('id', `${newRowId}`);
        fromRoomRow.dataset.hcalRoomObjId = refFromRoom.id;
      }
      if (refToRoom.overbooking || refToRoom.cancelled) {
        var cnumber = this.getExtraRoomRealNumber(refToRoom);
        refToRoom.id = refToRoomNewId;
        var newRowId = `${this._sanitizeId(`ROW_${cnumber}_${refFromRoom.type}_EXTRA${refFromReservs.id}`)}`;
        var elms = toRoomRow.querySelectorAll(`td[data-hcal-parent-row='${toRoomRow.id}']`);
        for (var elm of elms) { elm.dataset.hcalParentRow = newRowId; }
        toRoomRow.setAttribute('id', `${newRowId}`);
        toRoomRow.dataset.hcalRoomObjId = refToRoom.id;
      }

      for (var nreserv of fromReservations) {
        nreserv.cancelled = refToRoom.cancelled;
        nreserv.overbooking = refToRoom.overbooking;
        nreserv.room = refToRoom;
      }
      for (var nreserv of toReservations) {
        nreserv.cancelled = refFromRoom.cancelled;
        nreserv.overbooking = refFromRoom.overbooking;
        nreserv.room = refFromRoom;
      }
    } else {
       console.warn("[HotelCalendar][swapReservations] Invalid Swap Operation!");
      return false;
    }

    return true;
  },

  _dispatchSwapReservations: function() {
    if (this.reservationAction.inReservations.length > 0 && this.reservationAction.outReservations.length > 0) {
      this._dispatchEvent(
        'hcalOnSwapReservations',
        {
          'inReservs': this.reservationAction.inReservations || [],
          'outReservs': this.reservationAction.outReservations || [],
        }
      );
    }
  },

  _dispatchUnifyReservations: function() {
    if (this.reservationAction.hasOwnProperty('toUnify') && this.reservationAction.toUnify.length > 1) {
      this._dispatchEvent(
        'hcalOnUnifyReservations',
        {
          'toUnify': this.reservationAction.toUnify || [],
        }
      );
    }
  },

  replaceReservation: function(/*HReservationObject*/reservationObj, /*HReservationObject*/newReservationObj) {
    if (!reservationObj._html) {
      console.warn("[Hotel Calendar][updateReservation_] Invalid Reservation Object");
      return;
    }

    var index = _.findKey(this._reservations, {'id': reservationObj.id});
    delete this._reservations[index];
    this._reservations[index] = newReservationObj;
    reservationObj._html.dataset.hcalReservationObjId = newReservationObj.id;
    this._updateReservationsMap();
    this._updateDivReservation(newReservationObj);

    var linkedReservations = this.getLinkedReservations(newReservationObj);
    for (var lr of linkedReservations) {
      lr.startDate = newReservationObj.startDate.clone();
      lr.endDate = newReservationObj.endDate.clone();

      if (lr._html) {
        this._calcReservationCellLimits(lr);
        this._updateDivReservation(lr);
      }
    }
    _.defer(function(){ this._updateReservationOccupation(); }.bind(this));
  },

  getLinkedReservations: function(/*HReservationObject*/reservationObj) {
    return _.reject(this._reservations, function(item){ return item.linkedId !== reservationObj.id; });
  },

  _updateReservation: function(/*HReservationObject*/reservationObj, /*Bool?*/noRefresh) {
    // Fill
    if (reservationObj._limits.isValid()) {
      this._updateDivReservation(reservationObj, noRefresh);
    } else {
      console.warn(`[Hotel Calendar][_updateReservation] Can't place reservation ID@${reservationObj.id} [${reservationObj.startDate.format(HotelCalendar.DATE_FORMAT_LONG_)} --> ${reservationObj.endDate.format(HotelCalendar.DATE_FORMAT_LONG_)}]`);
      this.removeReservation(reservationObj);
    }
  },

  _updateReservations: function(/*Bool*/updateLimits) {
      for (var reservation of this._reservations){
        if (updateLimits) {
          this._calcReservationCellLimits(reservation);
        }
        this._updateReservation(reservation);
      }
      //this._assignReservationsEvents();
      //this._updateReservationOccupation();
      this._updateOBIndicators();
  },

  _assignReservationsEvents: function(reservDivs) {
    var $this = this;
    reservDivs = reservDivs || this.e.querySelectorAll('div.hcal-reservation');
    for (var rdiv of reservDivs) {
      var bounds = this.loopedOffsetOptimized(rdiv);
      rdiv.addEventListener('mousemove', function(ev){
        var posAction = $this._getRerservationPositionAction(this, ev.layerX, ev.layerY);
        if (posAction == HotelCalendar.ACTION.MOVE_LEFT || posAction == HotelCalendar.ACTION.MOVE_RIGHT) {
          this.style.cursor = 'col-resize';
        } else if (posAction == HotelCalendar.ACTION.MOVE_DOWN) {
          this.style.cursor = 'ns-resize';
        } else {
          this.style.cursor = 'pointer';
        }
      }, false);
      var _funcEvent = function(ev){
        if ($this._isLeftButtonPressed(ev)) {
          // MODE UNIFY RESERVATIONS
          if ($this._selectionMode === HotelCalendar.ACTION.UNIFY) {
            var reserv = $this.getReservation(this.dataset.hcalReservationObjId);
            var dateLimits = $this.getDateLimits($this.reservationAction.toUnify, false);
            var refUnifyReserv = ($this.reservationAction.toUnify.length > 0)?$this.reservationAction.toUnify[0]:false;
            if ($this.reservationAction.toUnify.indexOf(reserv) != -1) {
              $this.reservationAction.toUnify = _.reject($this.reservationAction.toUnify, function(item){ return item === reserv});
              this.classList.remove('hcal-reservation-unify-selected');
            }
            else {
              $this.reservationAction.toUnify.push(reserv);
              this.classList.add('hcal-reservation-unify-selected');
            }
            $this._updateHighlightUnifyReservations();
          }
          else {
            // ENABLE SWAP SELECTION
            if (ev.ctrlKey || $this._modeSwap === HotelCalendar.MODE.SWAP_FROM) {
              $this.reservationAction.action = HotelCalendar.ACTION.SWAP;
              $this.setSwapMode(HotelCalendar.MODE.SWAP_FROM);
            }
            // MODE SWAP RESERVATIONS
            if ($this.reservationAction.action === HotelCalendar.ACTION.SWAP) {
              var reserv = $this.getReservation(this.dataset.hcalReservationObjId);
              var refFromReserv = ($this.reservationAction.inReservations.length > 0)?$this.reservationAction.inReservations[0]:false;
              var refToReserv = ($this.reservationAction.outReservations.length > 0)?$this.reservationAction.outReservations[0]:false;

              if (ev.ctrlKey || $this._modeSwap === HotelCalendar.MODE.SWAP_FROM) {
                var canAdd = !((!refFromReserv && refToReserv && reserv.room.id === refToReserv.room.id) || (refFromReserv && reserv.room.id !== refFromReserv.room.id));
                // Can unselect
                if ($this.reservationAction.inReservations.indexOf(reserv) != -1 && (($this.reservationAction.outReservations.length > 0 && $this.reservationAction.inReservations.length > 1) || $this.reservationAction.outReservations.length === 0)) {
                  $this.reservationAction.inReservations = _.reject($this.reservationAction.inReservations, function(item){ return item === reserv});
                  this.classList.remove('hcal-reservation-swap-in-selected');
                }
                // Can't add a 'out' reservation in 'in' list
                else if ($this.reservationAction.outReservations.indexOf(reserv) == -1 && canAdd) {
                  $this.reservationAction.inReservations.push(reserv);
                  this.classList.add('hcal-reservation-swap-in-selected');
                }
              } else if (!ev.ctrlKey || $this._modeSwap === HotelCalendar.MODE.SWAP_TO) {
                $this.setSwapMode(HotelCalendar.MODE.SWAP_TO);
                var canAdd = !((!refToReserv && refFromReserv && reserv.room.id === refFromReserv.room.id) || (refToReserv && reserv.room.id !== refToReserv.room.id));
                // Can unselect
                if ($this.reservationAction.outReservations.indexOf(reserv) != -1) {
                  $this.reservationAction.outReservations = _.reject($this.reservationAction.outReservations, function(item){ return item === reserv; });
                  this.classList.remove('hcal-reservation-swap-out-selected');
                }
                // Can't add a 'in' reservation in 'out' list
                else if ($this.reservationAction.inReservations.indexOf(reserv) == -1 && canAdd) {
                  $this.reservationAction.outReservations.push(reserv);
                  this.classList.add('hcal-reservation-swap-out-selected');
                }
              }
              $this._updateHighlightSwapReservations();
            }
            // MODE RESIZE/MOVE RESERVATION
            else if (!$this.reservationAction.reservation) {
              $this.reservationAction = {
                reservation: this,
                mousePos: [ev.x, ev.y],
                action: $this._getRerservationPositionAction(this, ev.layerX, ev.layerY),
                inReservations: [],
                outReservations: [],
              };

              // FIXME: Workaround for lazy selection operation
              if ($this._lazyModeReservationsSelection) {
                clearTimeout($this._lazyModeReservationsSelection);
                $this._lazyModeReservationsSelection = false;
              }

              $this._lazyModeReservationsSelection = setTimeout(function($this){
                var reserv = $this.getReservation(this.dataset.hcalReservationObjId);
                $this._updateHighlightInvalidZones(reserv);
                if (reserv.readOnly || (reserv.fixDays && ($this.reservationAction.action == HotelCalendar.ACTION.MOVE_LEFT
                      || $this.reservationAction.action == HotelCalendar.ACTION.MOVE_RIGHT))) {
                  $this.reservationAction.action = HotelCalendar.ACTION.NONE;
                  return false;
                }
                var affectedReservations = [reserv].concat($this.getLinkedReservations(reserv));
                for (var areserv of affectedReservations) {
                  if (areserv._html) {
                    areserv._html.classList.add('hcal-reservation-action');
                  }
                }

                var otherReservs = _.difference($this._reservations, affectedReservations);
                for (var oreserv of otherReservs) {
                  if (oreserv._html) {
                    oreserv._html.classList.add('hcal-reservation-foreground');
                  }
                }

                $this._lazyModeReservationsSelection = false;
              }.bind(this, $this), 175);
            }
          }
        }
      };
      rdiv.addEventListener('mousedown', _funcEvent, this._supportsPassive ? { passive: true } : false);
      rdiv.addEventListener('touchstart', _funcEvent, this._supportsPassive ? { passive: true } : false);
      rdiv.addEventListener('click', function(ev){
        $this._dispatchEvent(
          'hcalOnClickReservation',
          {
            'event': ev,
            'reservationDiv': this,
            'reservationObj': $this.getReservation(this.dataset.hcalReservationObjId)
          });
      }, false);
      rdiv.addEventListener('dblclick', function(ev){
        $this._dispatchEvent(
          'hcalOnDblClickReservation',
          {
            'event': ev,
            'reservationDiv': this,
            'reservationObj': $this.getReservation(this.dataset.hcalReservationObjId)
          });
      }, false);
      /*
      rdiv.addEventListener('mouseenter', function(ev){
        $this._dispatchEvent(
          'hcalOnMouseEnterReservation',
          {
            'event': ev,
            'reservationDiv': this,
            'reservationObj': $this.getReservation(this.dataset.hcalReservationObjId)
          });
      }, false);
      rdiv.addEventListener('mouseleave', function(ev){
        $this._dispatchEvent(
          'hcalOnMouseLeaveReservation',
          {
            'event': ev,
            'reservationDiv': this,
            'reservationObj': $this.getReservation(this.dataset.hcalReservationObjId)
          });
      }, false);
      */
    }
  },

  _getRerservationPositionAction: function(/*HTMLObject*/elm, /*Int*/posX, /*Int*/posY) {
    var bounds = this.loopedOffsetOptimized(elm);
    if (posX <= 4) { return HotelCalendar.ACTION.MOVE_LEFT; }
    else if (posX >= bounds.width-8) { return HotelCalendar.ACTION.MOVE_RIGHT; }
    else if (posY >= bounds.height-4) { return HotelCalendar.ACTION.MOVE_DOWN; }
    return HotelCalendar.ACTION.MOVE_ALL;
  },

  _cleanUnusedZones: function(/*HReservationObject*/reserv) {
    var unusedReservs = this.getLinkedReservations(reserv);
    for (var unusedZone of unusedReservs) {
      if (unusedZone._html && unusedZone._html.parentNode) {
        unusedZone._html.parentNode.removeChild(unusedZone._html);
      }
    }
    this._reservations = _.reject(this._reservations, {unusedZone: true, linkedId: reserv.id});
  },

  _createUnusedZones: function(/*Array*/reservs) {
    var nreservs = [];
    for (var reserv of reservs) {
      if (!reserv.unusedZone) {
        var unused_id = 0;
        var numBeds = reserv.getTotalPersons(false);
      	for (var e=numBeds; e<reserv.room.capacity; ++e) {
      		nreservs.push(new HReservation({
            'id': `${reserv.id}@${--unused_id}`,
            'room': reserv.room,
            'title': '',
            'adults': 1,
            'childrens': 0,
            'startDate': reserv.startDate.clone(),
            'endDate': reserv.endDate.clone(),
            'color': '#c2c2c2',
            'colorText': '#c2c2c2',
            'splitted': false,
            'readOnly': true,
            'fixDays': true,
            'fixRooms': true,
            'unusedZone': true,
            'linkedId': reserv.id,
            'state': 'draft',
          }));
      	}
      }
    }
    return nreservs;
  },

  _updateReservationOccupation: function() {
    if (!this.options.showAvailability) {
      return;
    }
    var cells = [
      this.edtable.querySelectorAll('.hcal-cell-detail-room-free-type-group-item-day'),
      this.edtable.querySelectorAll('.hcal-cell-detail-room-free-total-group-item-day'),
      this.edtable.querySelectorAll('.hcal-cell-detail-room-perc-occup-group-item-day')
    ];

    for (var cell of cells[0]) {
      // Occupation by Type
      if (cell) {
        var cell_date = cell.dataset.hcalDate;
        var num_rooms_type = this._roomCapacities[cell.parentNode.dataset.hcalRoomType];
        var num_free = this.calcDayRoomTypeReservations(cell_date, cell.parentNode.dataset.hcalRoomType);
        cell.innerText = num_free;
        cell.style.backgroundColor = this._generateColor(num_free, num_rooms_type, 0.35, true, true);
      }
    }

    var cell;
    var num_rooms = this._roomCapacityTotal;
    for (var i=0; i<=this.options.days; ++i) {
      // Occupation Total
      cell = cells[1][i];
      var cell_date = cell.dataset.hcalDate;
      var num_free = this.calcDayRoomTotalReservations(cell_date);
      if (cell) {
        cell.innerText = num_free;
        cell.style.backgroundColor = this._generateColor(num_free, num_rooms, 0.35, true, true);
      }

      // Occupation Total Percentage
      cell = cells[2][i];
      if (cell) {
        var perc = 100.0 - (num_free * 100.0 / num_rooms);
        cell.innerText = perc.toFixed(0);
        cell.style.backgroundColor = this._generateColor(perc, 100.0, 0.35, false, true);
      }
    }
  },

  //==== PRICELIST
  getPricelist: function(onlyNew) {
    var data = {};

    var key = this._pricelist_id;
    var pricelist = this._pricelist[key];
    for (var listitem of pricelist) {
      for (var i=0; i<=this.options.days; ++i) {
        var dd = this.options.startDate.clone().local().startOf('day').add(i,'d').utc();
        var dd_local = dd.clone().local();

        var input = this.edtable.querySelector(`#${this._sanitizeId(`INPUT_PRICE_${key}_${listitem.room}_${dd_local.format(HotelCalendar.DATE_FORMAT_SHORT_)}`)}`);
        if (input.value !== input.dataset.orgValue) {
          var value = input.value;
          var orgValue = input.dataset.orgValue;
          var parentCell = this.edtable.querySelector(`#${input.dataset.hcalParentCell}`);
          var parentRow = this.edtable.querySelector(`#${parentCell.dataset.hcalParentRow}`);
          if (!(parentRow.dataset.hcalRoomTypeId in data)) { data[parentRow.dataset.hcalRoomTypeId] = []; }
          data[parentRow.dataset.hcalRoomTypeId].push({
            'date': HotelCalendar.toMoment(parentCell.dataset.hcalDate).format('YYYY-MM-DD'),
            'price': value
          });
        }
      }
    }

    return data;
  },

  setPricelist: function(/*List*/pricelist) {
    this._pricelist = pricelist;
    this._updatePriceList();
  },

  updateRoomTypePrice: function(pricelist_id, room_type_id, date, price) {
    var strDate = date.format(HotelCalendar.DATE_FORMAT_SHORT_);
    var cellId = this._sanitizeId(`CELL_PRICE_${pricelist_id}_${room_type_id}_${strDate}`);
    var input = this.edtable.querySelector(`#${cellId} input`);
    if (input) {
      input.dataset.orgValue = input.value = price;
      var pr_fk = _.findKey(this._pricelist[pricelist_id], {'room': room_type_id});
      this._pricelist[pricelist_id][pr_fk].days[strDate] = price;
    }
  },

  _updatePriceList: function() {
    if (!this.options.showPricelist) {
      return;
    }
    var keys = _.keys(this._pricelist);
    for (var k of keys) {
      var pr = this._pricelist[k];
      for (var pr_item of pr) {
        var pr_keys = _.keys(pr_item['days']);
        for (var prk of pr_keys) {
          var price = pr_item['days'][prk];
          var inputId = this._sanitizeId(`INPUT_PRICE_${k}_${pr_item['room']}_${prk}`);
          var input = this.edtable.querySelector(`#${inputId}`);
          if (input && !input.classList.contains('hcal-input-changed')) {
            input.value = input.dataset.orgValue = Number(price).toLocaleString();
          }
        }
      }
    }
  },

  //==== HELPER FUNCTIONS
  _isNumeric: function(/*?*/n) {
    return !isNaN(parseFloat(n)) && isFinite(n);
  },

  _in_domain: function(/*HRoomObject/HReservationObject*/obj, /*Array*/domain) {
    if (!domain || domain.length === 0) {
      return true;
    }

    var founded = false;
    for (var f of domain) {
      if (typeof f[2] === 'object' && f[2].length === 0) {
        continue;
      }

      var fieldName = f[0].toLowerCase();
      var compMode = f[1].toLowerCase();
      var userDataValue = obj.getUserData(fieldName) || false; // FIXME: Unused in some cases
      if (compMode === 'ilike') {
        var value = f[2].toLowerCase();
        var userData = userDataValue && userDataValue.toLowerCase() || '';
        if ((fieldName in obj && obj[fieldName].toLowerCase().search(value) !== -1) || userData.search(value) !== -1) {
          founded = true;
          //break;
        } else { return false; }
      } else if (compMode === '=') {
        if ((fieldName in obj && obj[fieldName] === f[2]) || userDataValue === f[2]) {
          founded = true;
          //break;
        } else { return false; }
      } else if (compMode === 'in') {
        if ((fieldName in obj && obj[fieldName] in f[2]) ||
            f[2].indexOf(userDataValue) != -1 ||
            (obj[fieldName] && typeof obj[fieldName] === 'object' && _.every(f[2], function(item) { return obj[fieldName].indexOf(item) !== -1; })) ||
            (userDataValue && typeof userDataValue === 'object' && userDataValue.length && _.every(f[2], function(item) { return userDataValue.indexOf(item) !== -1; }))) {
          founded = true;
          //break;
        } else { return false; }
      } else if (compMode === 'some') {
        if ((fieldName in obj && obj[fieldName] in f[2]) ||
            f[2].indexOf(userDataValue) != -1 ||
            (obj[fieldName] && typeof obj[fieldName] === 'object' && _.some(f[2], function(item) { return obj[fieldName].indexOf(item) !== -1; })) ||
            (userDataValue && typeof userDataValue === 'object' && userDataValue.length && _.some(f[2], function(item) { return userDataValue.indexOf(item) !== -1; }))) {
          founded = true;
          //break;
        } else { return false; }
      }
    }

    return founded;
  },

  getDateDiffDays: function(/*MomentObject*/start, /*MomentObject*/end) {
	  return end.diff(start, 'days');
  },

  getDateLimits: function(/*List HReservationObject*/reservs, /*Bool?*/noCheckouts) {
    var start_date = false;
    var end_date = false;
    for (var creserv of reservs) {
      if (!start_date) { start_date = creserv.startDate.clone(); }
      else if (creserv.startDate.isBefore(start_date, 'day')) {
        start_date = creserv.startDate.clone();
      }
      if (!end_date) { end_date = creserv.endDate.clone(); }
      else if (creserv.endDate.isAfter(end_date, 'day')) {
        end_date = creserv.endDate.clone();
      }

      if (noCheckouts) {
        end_date.subtract(1, 'd');
      }
    }

    return [start_date, end_date];
  },

  getFreeDatesByRoom: function(/*MomentObject*/dateStart, /*MomentObject*/dateEnd, /*Int*/roomId) {
    var daysLeft = this.getDateDiffDays(this.options.startDate, dateStart);
    var daysRight = this.getDateDiffDays(dateEnd, this._endDate);
    var freeDates = [dateStart, dateEnd];

    var ndate = dateStart.clone();
    for (var i=1; i<daysLeft; i++) {
      ndate.subtract(1, 'd');
      var reservs = this.getReservationsByDay(ndate, true, false, roomId);
      if (reservs.length != 0) { break; }
      freeDates[0] = ndate.clone();
    }
    ndate = dateEnd.clone();
    for (var i=1; i<daysRight; i++) {
      ndate.add(1, 'd');
      var reservs = this.getReservationsByDay(ndate, true, false, roomId);
      if (reservs.length != 0) { break; }
      freeDates[1] = ndate.clone();
    }

    return freeDates;
  },

  _dispatchEvent: function(/*String*/eventName, /*Dictionary*/data) {
    this.e.dispatchEvent(new CustomEvent(eventName, {
      detail: _.extend({calendar_obj: this}, data),
    }));
  },

  _sanitizeId: function(/*String*/str) {
    return str.replace(/[^a-zA-Z0-9\-_]/g, '_');
  },

  _isLeftButtonPressed: function(/*EventObject*/evt) {
    evt = evt || window.event;
    if (evt.touched && evt.touched.length) {
      return true;
    }
    return ("buttons" in evt)?(evt.buttons === 1):(evt.which || evt.button);
  },

  _t: function(/*String*/str) {
    if (str in this._strings) {
      return this._strings[str];
    }
    return str;
  },

  toAbbreviation: function(/*String*/word, /*Int*/max) {
    return word.replace(/[aeiouáéíóúäëïöü]/gi,'').toUpperCase().substr(0, max || 3);
  },

  checkReservationPlace: function(/*HReservationObject*/reservationObj) {
    var persons = reservationObj.getTotalPersons(false);
    if (((reservationObj.room.shared || this.options.divideRoomsByCapacity) && reservationObj._beds.length < persons)
      || (!(reservationObj.room.shared || this.options.divideRoomsByCapacity) && persons > reservationObj.room.capacity)) {
      return false;
    }

    if (reservationObj.room.id in this._reservationsMap) {
      for (var r of this._reservationsMap[reservationObj.room.id]) {
        if (!r.unusedZone && r !== reservationObj && reservationObj.room.number == r.room.number &&
            (_.difference(reservationObj._beds, r._beds).length != reservationObj._beds.length || this.options.divideRoomsByCapacity) &&
            (r.startDate.isBetween(reservationObj.startDate, reservationObj.endDate, 'day', '[)') ||
              r.endDate.isBetween(reservationObj.startDate, reservationObj.endDate, 'day', '(]') ||
              (reservationObj.startDate.isSameOrAfter(r.startDate, 'day') && reservationObj.endDate.isSameOrBefore(r.endDate, 'day')))) {
          return false;
        }
      }
    }

    return true;
  },

  getDates: function() {
    return [this.options.startDate.clone(), this._endDate.clone()];
  },

  //==== EVENT FUNCTIONS
  _onInputChange: function(/*EventObject*/ev, /*HTMLObject*/elm) {
    //var parentCell = this.edtable.querySelector(`#${elm.dataset.hcalParentCell}`);
    //var parentRow = this.edtable.querySelector(`#${parentCell.dataset.hcalParentRow}`);
    var value = elm.value;
    var orgValue = elm.dataset.orgValue;
    var name = elm.getAttribute('name');

    if (name === 'room_type_price_day') {
      if (!this._isNumeric(value)) {
        elm.style.backgroundColor = 'red';
      } else if (orgValue !== value) {
        elm.classList.add('hcal-input-changed');
        elm.style.backgroundColor = '';
      } else {
        elm.classList.remove('hcal-input-changed');
        if (value == 0) {
          elm.style.backgroundColor = 'rgb(255, 174, 174)';
        }
      }
    }

    var parentCell = this.edtable.querySelector(`#${elm.dataset.hcalParentCell}`);
    var parentRow = this.edtable.querySelector(`#${parentCell.dataset.hcalParentRow}`);
    var vals = {
      'room_type_id': +parentRow.dataset.hcalRoomTypeId,
      'date': HotelCalendar.toMoment(parentCell.dataset.hcalDate),
      'price': value,
      'old_price': orgValue,
      'pricelist_id': +parentRow.dataset.hcalPricelist
    };
    //this.updateRoomTypePrice(vals['pricelist_id'], vals['room_type_id'], vals['date'], vals['price']);
    this._dispatchEvent('hcalOnPricelistChanged', vals);

    if (this.edivc.querySelector('.hcal-input-changed') !== null)
    {
      this.btnSaveChanges.classList.add('need-save');
      this.btnSaveChanges.disabled = false;
    } else {
      this.btnSaveChanges.classList.remove('need-save');
      this.btnSaveChanges.disabled = true;
    }
  },

  _onCellMouseUp: function(ev) {
    if (this._selectionMode === HotelCalendar.ACTION.DIVIDE) {
      if (this.reservationAction.reservation) {
        var realEndDate = this.reservationAction.endDate.clone().subtract(1, 'd');
        if (this.reservationAction.action === HotelCalendar.ACTION.DIVIDE && !this.reservationAction.date.isSame(realEndDate, 'day')) {
          var diff = this.getDateDiffDays(this.reservationAction.date, realEndDate);
          this._dispatchEvent('hcalOnSplitReservation', {
            reservation: this.reservationAction.reservation,
            obj_id: this.reservationAction.obj_id,
            date: this.reservationAction.date,
            nights: diff
          })
          this._reset_action_reservation();
          this.setSelectionMode(HotelCalendar.ACTION.NONE);
        }
      }
    }
    else if (this.reservationAction.action !== HotelCalendar.ACTION.NONE) {
      return;
    }
    else if (this._cellSelection.start &&
             this._cellSelection.start.dataset.hcalParentRow === ev.target.dataset.hcalParentRow) {
      this._cellSelection.end = ev.target;
      this._dispatchEvent(
        'hcalOnChangeSelection',
        {
          'cellStart': this._cellSelection.start,
          'cellEnd': this._cellSelection.end
        });
    }
  },

  _onCellMouseDown: function(ev) {
    if (this._selectionMode === HotelCalendar.ACTION.DIVIDE && this._splitReservation) {
      this.reservationAction = {
        reservation: this._splitReservation._html,
        obj_id: this._splitReservation.id,
        endDate: this._splitReservation.endDate,
        action: this._selectionMode,
        date: this._splitDate,
      };
      this._splitReservation = false;
      this._splitDate = false;
    } else if ($(".marked-as-having-a-popover").length === 1) {
      // TODO: better call _destroy_and_clear_popover_mark defined in hotel_calendar_controller.js
      $(".marked-as-having-a-popover").popover('destroy');
      $('.hcal-reservation').removeClass("marked-as-having-a-popover");
    } else {
      // FIXME: Prevent multiple clicks in a row
      this._cellSelection.start = this._cellSelection.current = ev.target;
      this._cellSelection.end = false;
      this._updateCellSelection();
    }
  },

  _onCellMouseEnter: function(ev) {
    var date_cell = HotelCalendar.toMoment(this.etable.querySelector(`#${ev.target.dataset.hcalParentCell}`).dataset.hcalDate);
    var reserv;
    if (this.reservationAction.reservation) {
      reserv = this.getReservation(this.reservationAction.reservation.dataset.hcalReservationObjId);
      if (!this.reservationAction.oldReservationObj) {
        this.reservationAction.oldReservationObj = reserv.clone();
        this.reservationAction.daysOffset = this.getDateDiffDays(reserv.startDate.clone().local(), date_cell);
        if (this.reservationAction.daysOffset < 0 ) {
          this.reservationAction.daysOffset = 0;
        }
      }
    }
    if (this._selectionMode === HotelCalendar.MODE.NONE && this._isLeftButtonPressed(ev)) {
      var toRoom = undefined;
      var needUpdate = false;
      if (!this.reservationAction.reservation) {
        if (this._cellSelection.start && this._cellSelection.start.dataset.hcalParentRow === ev.target.dataset.hcalParentRow) {
          this._cellSelection.current = ev.target;
        }
        this._updateCellSelection();
      } else if (this.reservationAction.mousePos) {
        // workarround for not trigger reservation change
        var a = this.reservationAction.mousePos[0] - ev.x;
        var b = this.reservationAction.mousePos[1] - ev.y;
        //var dist = Math.sqrt(a*a + b*b);
        if (this.reservationAction.action == HotelCalendar.ACTION.MOVE_RIGHT) {
          if (reserv.fixDays) {
            this._reset_action_reservation();
            return true;
          }
          if (!date_cell.isAfter(reserv.startDate, 'd')) {
            date_cell = reserv.startDate.clone().startOf('day');
          }
          if (!this.reservationAction.oldReservationObj) {
            this.reservationAction.oldReservationObj = reserv.clone();
          }
          reserv.endDate.set({'date': date_cell.date(), 'month': date_cell.month(), 'year': date_cell.year()}).add(1, 'd');
          this.reservationAction.newReservationObj = reserv;
          needUpdate = true;
        } else if (this.reservationAction.action == HotelCalendar.ACTION.MOVE_LEFT) {
          if (reserv.fixDays) {
            this._reset_action_reservation();
            return true;
          }
          var ndate = reserv.endDate.clone().endOf('day').subtract(1, 'd');
          if (!date_cell.isBefore(ndate, 'd')) {
            date_cell = ndate;
          }
          if (!this.reservationAction.oldReservationObj) {
            this.reservationAction.oldReservationObj = reserv.clone();
          }
          reserv.startDate.set({'date': date_cell.date(), 'month': date_cell.month(), 'year': date_cell.year()});
          this.reservationAction.newReservationObj = reserv;
          needUpdate = true;
        } else if (this.reservationAction.action == HotelCalendar.ACTION.MOVE_DOWN) {
          var parentRow = ev.target.parentNode.parentNode.parentNode.parentNode;
          var room = this.getRoom(parentRow.dataset.hcalRoomObjId);

          if (room.id === reserv.room.id) {
            if (!this.reservationAction.oldReservationObj) {
              this.reservationAction.oldReservationObj = reserv.clone();
            }
            reserv.adults = +ev.target.dataset.hcalBedNum + 1;
            this.reservationAction.newReservationObj = reserv;
            needUpdate = true;
          }
        } else if (this.reservationAction.action == HotelCalendar.ACTION.MOVE_ALL) {
          // Relative Movement
          date_cell.subtract(this.reservationAction.daysOffset, 'd');

          var parentRow = ev.target.parentNode.parentNode.parentNode.parentNode;
          var room = this.getRoom(parentRow.dataset.hcalRoomObjId);
          reserv.room = room;
          var diff_date = this.getDateDiffDays(reserv.startDate, reserv.endDate);
          reserv.startDate.set({'date': date_cell.date(), 'month': date_cell.month(), 'year': date_cell.year()});
          var date_end = reserv.startDate.clone().add(diff_date, 'd');
          reserv.endDate.set({'date': date_end.date(), 'month': date_end.month(), 'year': date_end.year()});
          this.reservationAction.newReservationObj = reserv;
          toRoom = +ev.target.dataset.hcalBedNum;
          needUpdate = true;
        }
      }

      if (needUpdate && reserv) {
        _.defer(function(r){ this._updateScroll(r._html); }.bind(this), reserv)

        var affectedReservations = [reserv].concat(this.getLinkedReservations(this.reservationAction.newReservationObj));
        for (var areserv of affectedReservations) {
          if (areserv !== reserv) {
            areserv.startDate = reserv.startDate.clone();
            areserv.endDate = reserv.endDate.clone();
          }

          if (areserv._html) {
            if (areserv.unusedZone) {
              areserv._html.style.visibility = 'hidden';
              continue;
            }
            _.defer(function(ro, r, tro){
              this._calcReservationCellLimits(
                r,
                r===ro?tro:undefined,
                !this.options.assistedMovement);
              this._updateDivReservation(r);

              if (!r._limits.isValid() || !this.checkReservationPlace(r) ||
                  (r.fixRooms && this.reservationAction.oldReservationObj.room.id != r.room.id) ||
                  (r.fixDays && !this.reservationAction.oldReservationObj.startDate.isSame(r.startDate, 'day'))) {
                r._html.classList.add('hcal-reservation-invalid');
              }
              else {
                r._html.classList.remove('hcal-reservation-invalid');
              }
            }.bind(this), reserv, areserv, toRoom);
          }
        }
      }
    } else if (this._selectionMode === HotelCalendar.ACTION.DIVIDE) {
      var parentRow = ev.target.parentNode.parentNode.parentNode.parentNode;
      var room_id = parentRow.dataset.hcalRoomObjId;
      var reservs = this.getReservationsByDay(date_cell, true, false, room_id);
      if (this._divideDivs) {
        this._divideDivs[0].remove();
        this._divideDivs[1].remove();
        this._divideDivs = false;
      }
      if (reservs.length) {
        this._splitReservation = reservs[0];
        var defStyle = {
          top: this._splitReservation._html.style.top,
          left: this._splitReservation._html.style.left,
          height: this._splitReservation._html.style.height,
        };
        this._divideDivs = [
            $('<div/>', {class: 'hcal-reservation-divide-l', css: defStyle}).appendTo(this.edivr),
            $('<div/>', {class: 'hcal-reservation-divide-r', css: defStyle}).appendTo(this.edivr)
        ];
        var diff = this.getDateDiffDays(this._splitReservation.startDate, date_cell);
        var boundsCell = false;
        var beginCell = this.loopedOffsetOptimized(this._splitReservation._limits.left);
        var endCell = this.loopedOffsetOptimized(this._splitReservation._limits.right);
        this._splitDate = date_cell.clone();
        if (date_cell.isSame(this._splitReservation.endDate.clone().subtract(1, 'd'), 'day')) {
          this._splitDate.subtract(1, 'd');
          var tcell = this.getCell(this._splitDate, this._splitReservation.room, 0);
          if (tcell) {
            boundsCell = this.loopedOffsetOptimized(tcell);
          } else {
            boundsCell = false;
            this._splitReservation = false;
            this._splitDate = false;
          }
        } else {
          boundsCell = this.loopedOffsetOptimized(ev.target);
        }
        if (boundsCell) {
          this._divideDivs[0][0].style.width = `${(boundsCell.left-beginCell.left)+boundsCell.width}px`;
          this._divideDivs[1][0].style.left = `${(boundsCell.left-this._etableOffset.left)+boundsCell.width}px`;
          this._divideDivs[1][0].style.width = `${(endCell.left-boundsCell.left)}px`;
        }
      } else {
        this._splitReservation = false;
        this._splitDate = false;
      }
    }
  },

  onMainKeyUp: function(/*EventObject*/ev) {
    if (this.reservationAction.action === HotelCalendar.ACTION.SWAP || this.getSwapMode() !== HotelCalendar.MODE.NONE) {
      var needReset = false;
      if (ev.keyCode === 27) {
        this.cancelSwap();
      }
      else if (ev.keyCode === 13) {
        this._dispatchSwapReservations();
        this._reset_action_reservation();
        this._updateHighlightSwapReservations();
        this._modeSwap = HotelCalendar.MODE.NONE;
      }
      else if (ev.keyCode === 17 && this.getSwapMode() === HotelCalendar.MODE.SWAP_FROM) {
        this.setSwapMode(HotelCalendar.MODE.SWAP_TO);
      }
    } else if (this._selectionMode !== HotelCalendar.MODE.NONE) {
      if (this._selectionMode === HotelCalendar.ACTION.UNIFY && (ev.keyCode === 13 || ev.keyCode === 27)) {
        if (ev.keyCode === 13) {
          this._dispatchUnifyReservations();
        }
        this._reset_action_reservation();
        this._updateHighlightUnifyReservations();
      }

      if (ev.keyCode === 27 || ev.keyCode === 13) {
        this.setSelectionMode(HotelCalendar.MODE.NONE);
      }
    }
  },

  onMainKeyDown: function(/*EventObject*/ev) {
    if (this.reservationAction.action === HotelCalendar.ACTION.SWAP || this.getSwapMode() !== HotelCalendar.MODE.NONE) {
      if (ev.keyCode === 17 && this.getSwapMode() === HotelCalendar.MODE.SWAP_TO) {
        this.setSwapMode(HotelCalendar.MODE.SWAP_FROM);
      }
    }
  },

  onMainMouseUp: function(/*EventObject*/ev) {
    if (this._lazyModeReservationsSelection) {
      clearTimeout(this._lazyModeReservationsSelection);
      this._lazyModeReservationsSelection = false;
    }
    _.defer(function(ev){
      if (this.reservationAction.reservation) {
          var reservDiv = this.reservationAction.reservation;
          reservDiv.classList.remove('hcal-reservation-action');
          this._updateHighlightInvalidZones();

          var rdivs = this.e.querySelectorAll('div.hcal-reservation.hcal-reservation-foreground');
          for (var rd of rdivs) { rd.classList.remove('hcal-reservation-foreground'); }

          var reserv = this.getReservation(reservDiv.dataset.hcalReservationObjId);
          var linkedReservations = this.getLinkedReservations(reserv);
          var hasInvalidLink = false;
          for (var r of linkedReservations) {
            if (r._html) {
              hasInvalidLink = !hasInvalidLink && r._html.classList.contains('hcal-reservation-invalid');
              r._html.classList.remove('hcal-reservation-action');
              r._html.classList.remove('hcal-reservation-invalid');
              r._html.style.visibility = '';
            }
          }

          if (this.reservationAction.oldReservationObj && this.reservationAction.newReservationObj) {
            if (!this.options.allowInvalidActions && (reservDiv.classList.contains('hcal-reservation-invalid') || hasInvalidLink)) {
              this.replaceReservation(this.reservationAction.newReservationObj, this.reservationAction.oldReservationObj);
            } else {
              var oldReservation = this.reservationAction.oldReservationObj;
              var newReservation = this.reservationAction.newReservationObj;
              // Calc Old Reservation Price
              var oldDiff = this.getDateDiffDays(oldReservation.startDate, oldReservation.endDate);
              var oldPrice = 0.0
              for (var e=0; e<oldDiff; e++) {
                var ndate = oldReservation.startDate.clone().add(e, 'd');
                oldPrice += this.getRoomPrice(oldReservation.room, ndate);
              }
              // Calc New Reservation Price
              var newDiff = this.getDateDiffDays(newReservation.startDate, newReservation.endDate);
              var newPrice = 0.0
              for (var e=0; e<newDiff; e++) {
                var ndate = newReservation.startDate.clone().add(e, 'd');
                newPrice += this.getRoomPrice(newReservation.room, ndate);
              }

              this._dispatchEvent(
                'hcalOnChangeReservation',
                {
                  'oldReserv': oldReservation,
                  'newReserv': newReservation,
                  'oldPrice': oldPrice,
                  'newPrice': newPrice
                });
              _.defer(function(){ this._updateReservationOccupation(); }.bind(this));
            }
            reservDiv.classList.remove('hcal-reservation-invalid');
          } else {
            /*
            this._dispatchEvent(
              'hcalOnDblClickReservation',
              {
                'event': ev,
                'reservationDiv': reservDiv,
                'reservationObj': reserv
              });
              */
          }

          this._reset_action_reservation();
      }
      this._resetCellSelection();
      this._updateCellSelection();
    }.bind(this), ev);
  },

  onMainResize: function(/*EventObject*/ev) {
    _.defer(function(){
      this._updateOffsets();
      this._updateReservations();
    }.bind(this));
  },

  //=== OPTIMIZED OFFSET
  // Method from https://jsperf.com/offset-vs-getboundingclientrect/7
  loopedOffsetOptimized: function (elem) {
    var offsetLeft = elem.offsetLeft
      , offsetTop = elem.offsetTop
      , offsetWidth = elem.offsetWidth
      , offsetHeight = elem.offsetHeight
      , lastElem = elem;

    while (elem = elem.offsetParent) {
      if (elem === document.body) { //from my observation, document.body always has scrollLeft/scrollTop == 0
        break;
      }
      offsetLeft += elem.offsetLeft;
      offsetTop += elem.offsetTop;
      lastElem = elem;
    }
    // if (lastElem && lastElem.style.position === 'fixed') { //slow - http://jsperf.com/offset-vs-getboundingclientrect/6
    //   //if(lastElem !== document.body) { //faster but does gives false positive in Firefox
    //   offsetLeft += window.pageXOffset || document.documentElement.scrollLeft;
    //   offsetTop += window.pageYOffset || document.documentElement.scrollTop;
    // }
    return {
      left: offsetLeft,
      top: offsetTop,
      width: offsetWidth,
      height: offsetHeight,
    };
  },

  //==== COLOR FUNCTIONS (RANGE: 0.0|1.0)
  _intToRgb: function(/*Int*/RGBint) {
    return [(RGBint >> 16) & 255, (RGBint >> 8) & 255, RGBint & 255];
  },

  _hueToRgb: function(/*Int*/v1, /*Int*/v2, /*Int*/h) {
    if (h<0.0) { h+=1; }
    if (h>1.0) { h-=1; }
    if ((6.0*h) < 1.0) { return v1+(v2-v1)*6.0*h; }
    if ((2.0*h) < 1.0) { return v2; }
    if ((3.0*h) < 2.0) { return v1+(v2-v1)*((2.0/3.0)-h)*6.0; }
    return v1;
  },

  _hslToRgb: function(/*Int*/h, /*Int*/s, /*Int*/l) {
    if (s == 0.0) {
      return [l,l,l];
    }
    var v2 = l<0.5?l*(1.0+s):(l+s)-(s*l);
    var v1 = 2.0*l-v2;
    return [
      this._hueToRgb(v1,v2,h+(1.0/3.0)),
      this._hueToRgb(v1,v2,h),
      this._hueToRgb(v1,v2,h-(1.0/3.0))];
  },

  _RGBToHex: function(/*Int*/r, /*Int*/g, /*Int*/b){
    var bin = r << 16 | g << 8 | b;
    return (function(h){
      return new Array(7-h.length).join("0")+h;
    })(bin.toString(16).toUpperCase());
  },

  _hexToRGB: function(/*Int*/hex){
    var r = hex >> 16;
    var g = hex >> 8 & 0xFF;
    var b = hex & 0xFF;
    return [r,g,b];
  },

  _generateColor: function(/*Int*/value, /*Int*/max, /*Int*/offset, /*Bool*/reverse, /*Bool*/strmode) {
    var rgb = [offset,1.0,0.5];
    if (value > max) {
      if (!strmode) {
        return rgb;
      }
      return "rgb("+Math.floor(rgb[0]*255)+","+Math.floor(rgb[1]*255)+","+Math.floor(rgb[2]*255)+")";
    }
    if (reverse) {
      value = max-value;
    }
    rgb = this._hslToRgb(((max-value)*offset)/max, 1.0, 0.8);
    if (!strmode) {
      return rgb;
    }
    return "rgb("+Math.floor(rgb[0]*255)+","+Math.floor(rgb[1]*255)+","+Math.floor(rgb[2]*255)+")";
  }
};

/** CONSTANTS **/
HotelCalendar.DOMAIN = { NONE: -1, RESERVATIONS: 0, ROOMS: 1 };
HotelCalendar.ACTION = { NONE: -1, MOVE_ALL: 0, MOVE_LEFT: 1, MOVE_RIGHT: 2, MOVE_DOWN: 3, SWAP: 4, DIVIDE: 5, UNIFY: 6 };
HotelCalendar.MODE = { NONE: -1, SWAP_FROM: 0, SWAP_TO: 1 };
HotelCalendar.DATE_FORMAT_SHORT_ = 'DD/MM/YYYY';
HotelCalendar.DATE_FORMAT_LONG_ = HotelCalendar.DATE_FORMAT_SHORT_ + ' HH:mm:ss';
/** STATIC METHODS **/
HotelCalendar.toMoment = function(/*String,MomentObject*/ndate, /*String*/format) {
  if (moment.isMoment(ndate)) {
    return ndate;
  } else if (typeof ndate === 'string' || ndate instanceof Date) {
    ndate = moment(ndate, typeof format==='undefined'?HotelCalendar.DATE_FORMAT_LONG_:format);
    if (moment.isMoment(ndate)) {
      return ndate;
    }
  }

  //debugger;
  console.warn('[Hotel Calendar][toMoment] Invalid date format!');
  return false;
}
HotelCalendar.toMomentUTC = function(/*String,MomentObject*/ndate, /*String*/format) {
  if (moment.isMoment(ndate)) {
    return ndate;
  } else if (typeof ndate === 'string' || ndate instanceof Date) {
    ndate = moment.utc(ndate, (typeof format==='undefined'?HotelCalendar.DATE_FORMAT_LONG_:format));
    if (moment.isMoment(ndate)) {
      return ndate;
    }
  }

  //debugger;
  console.warn('[Hotel Calendar][toMomentUTC] Invalid date format!');
  return false;
}


/** ROOM OBJECT **/
function HRoom(/*Int*/id, /*String*/number, /*Int*/capacity, /*String*/type, /*Bool*/shared, /*List*/price) {
  this.id = id || -1;
  this.number = number || -1;
  this.capacity = capacity || 1;
  this.type = type || '';
  this.shared = shared;
  this.price = price || false;
  this.overbooking = false;
  this.cancelled = false;

  this._html = false;
  this._active = true;
  this._userData = {};
}
HRoom.prototype = {
  clearUserData: function() { this._userData = {}; },
  getUserData: function(/*String?*/key) {
    if (typeof key === 'undefined') {
      return this._userData;
    }
    return key in this._userData && this._userData[key] || null;
  },
  addUserData: function(/*Dictionary*/data) {
    if (!_.isObject(data)) {
      console.warn("[Hotel Calendar][HRoom][setUserData] Invalid Data! Need be a object!");
    } else {
      this._userData = _.extend(this._userData, data);
    }
  },
  clone: function() {
    var nroom = new HRoom(
        this.id,
        this.number,
        this.capacity,
        this.type,
        this.shared,
        this.price
    );
    nroom.overbooking = this.overbooking;
    nroom.cancelled = this.cancelled;
    nroom._html = this._html;
    nroom._active = this._active;
    nroom.addUserData(this.getUserData());
    return nroom;
  }
};

/** RESERVATION OBJECT **/
function HReservation(/*Dictionary*/rValues) {
  if (typeof rValues.room_id === 'undefined' && typeof rValues.room === 'undefined') {
    delete this;
    console.warn("[Hotel Calendar][HReservation] room can't be empty!");
    return;
  }

  this.id = rValues.id;
  this.room_id = rValues.room_id;
  this.adults = rValues.adults || 1;
  this.childrens = rValues.childrens || 0;
  this.title = rValues.title || '';
  this.startDate = rValues.startDate || null;
  this.endDate = rValues.endDate || null;
  this.color = rValues.color || '#000';
  this.colorText = rValues.colorText || '#FFF';
  this.readOnly = rValues.readOnly || false;
  this.fixRooms = rValues.fixRooms || false;
  this.fixDays = rValues.fixDays || false;
  this.unusedZone = rValues.unusedZone || false;
  this.linkedId = rValues.linkedId || -1;
  this.splitted = rValues.splitted || false;
  this.overbooking = rValues.overbooking || false;
  this.cancelled = rValues.cancelled || false;
  this.room = rValues.room || null;
  this.total_reservation = rValues.total_reservation || 0;
  this.total_folio = rValues.total_folio || 0;

  this._drawModes = ['hard-start', 'hard-end'];
  this._html = false;
  this._limits = new HLimit();
  this._beds = [];
  this._active = true;
  this._userData = {};
}
HReservation.prototype = {
  setRoom: function(/*HRoomObject*/room) { this.room = room; },
  setStartDate: function(/*String,MomentObject*/date) { this.startDate = HotelCalendar.toMoment(date); },
  setEndDate: function(/*String,MomentObject*/date) { this.endDate = HotelCalendar.toMoment(date); },

  clearUserData: function() { this._userData = {}; },
  getUserData: function(/*String?*/key) {
    if (typeof key === 'undefined') {
      return this._userData;
    }
    return key in this._userData && this._userData[key] || null;
  },
  addUserData: function(/*Dictionary*/data) {
    if (!_.isObject(data)) {
      console.warn("[Hotel Calendar][HReservation][setUserData] Invalid Data! Need be a object!");
    } else {
      this._userData = _.extend(this._userData, data);
    }
  },
  getTotalPersons: function(/*Boolean*/countChildrens) {
    var persons = this.adults;
    if (countChildrens) {
      persons += this.childrens;
    }
    return persons;
  },
  clone: function() {
    var nreserv = new HReservation({
      'id': this.id,
      'room': this.room?this.room.clone():null,
      'adults': this.adults,
      'childrens': this.childrens,
      'title': this.title,
      'startDate': this.startDate.clone(),
      'endDate': this.endDate.clone(),
      'color': this.color,
      'colorText': this.colorText,
      'readOnly': this.readOnly,
      'fixRooms': this.fixRooms,
      'fixDays': this.fixDays,
      'unusedZone': this.unusedZone,
      'linkedId': this.linkedId,
      'splitted': this.splitted,
      'overbooking': this.overbooking,
      'cancelled': this.cancelled,
      'room_id': this.room_id,
      'total_reservation': this.total_reservation,
      'total_folio': this.total_folio,
    });
    nreserv._beds = _.clone(this._beds);
    nreserv._html = this._html;
    nreserv._drawModes = _.clone(this._drawModes);
    nreserv._limits = this._limits.clone();
    nreserv._active = this._active;
    nreserv.addUserData(this.getUserData());
    return nreserv;
  }
};

/** LIMIT OBJECT **/
function HLimit(/*HTMLObject*/left, /*HMTLObject*/right) {
  this.left = left;
  this.right = right;
}
HLimit.prototype = {
  isSame: function() {
    return this.left == this.right;
  },
  isValid: function() {
    return this.left && this.right;
  },
  swap: function() {
    var tt = this.left;
    this.left = this.right;
    this.right = tt;
  },
  clone: function() {
    return new HLimit(this.left, this.right);
  }
};
